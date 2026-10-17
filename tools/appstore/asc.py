#!/usr/bin/env python3
"""Changes to Elm Lab's App Store listing, kept in the repository and sent with the App Store Connect API.

    asc.py check   [--screenshots DIR]                 checks the texts and screenshots, no key needed
    asc.py listing --version 1.1.0 [--screenshots DIR] applies them to that version

Most of the listing was filled in by hand in App Store Connect, so the repository holds only what
the script should set, and everything else is left as it is there:

- appstore/metadata/<locale>/<field>.txt: one file per text. A field without a file keeps its
  current value; a language App Store Connect does not have yet is added.
- appstore/app.json: the release type of the version.
- DIR/<locale>/*.png: screenshots, in upload order. Their pixel size decides the set (iPhone 6.9"
  or iPad 13"); a set that is given replaces the one in App Store Connect, and sets that are not
  given are left alone.

`listing` can run any number of times: it changes only what differs. A version without a build
gets the newest processed one of that version. Submitting for review and releasing are left to
App Store Connect itself, where they are one click each and cannot be taken back.

The key comes from the environment (ASC_KEY_ID, ASC_ISSUER_ID, ASC_KEY_P8), as in the release
workflow.
"""

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
APPSTORE = os.path.join(ROOT, "appstore")
API = "https://api.appstoreconnect.apple.com"

#Text files and where they go: (resource, attribute, character limit)
FIELDS = {
    "name": ("appInfoLocalizations", "name", 30),
    "subtitle": ("appInfoLocalizations", "subtitle", 30),
    "privacy_url": ("appInfoLocalizations", "privacyPolicyUrl", None),
    "description": ("appStoreVersionLocalizations", "description", 4000),
    "keywords": ("appStoreVersionLocalizations", "keywords", 100),
    "promotional_text": ("appStoreVersionLocalizations", "promotionalText", 170),
    "support_url": ("appStoreVersionLocalizations", "supportUrl", None),
    "marketing_url": ("appStoreVersionLocalizations", "marketingUrl", None),
}

#Pixel sizes App Store Connect takes for each screenshot set, in portrait
DISPLAYS = {
    "APP_IPHONE_67": [(1320, 2868), (1290, 2796), (1260, 2736)],
    "APP_IPAD_PRO_3GEN_129": [(2064, 2752), (2048, 2732)],
}
MAX_SCREENSHOTS = 10

EDITABLE_VERSION_STATES = {
    "PREPARE_FOR_SUBMISSION", "DEVELOPER_REJECTED", "REJECTED", "METADATA_REJECTED",
    "INVALID_BINARY",
}


def log(message):
    print(message, flush=True)


def fail(message):
    print(f"::error::{message}", flush=True)
    sys.exit(1)


#Repository side

def read_app():
    with open(os.path.join(APPSTORE, "app.json"), encoding="utf-8") as f:
        return json.load(f)


def read_metadata():
    base = os.path.join(APPSTORE, "metadata")
    metadata = {}
    for locale in sorted(os.listdir(base)):
        folder = os.path.join(base, locale)
        if not os.path.isdir(folder):
            continue
        texts = {}
        for name in sorted(os.listdir(folder)):
            if name.endswith(".txt"):
                with open(os.path.join(folder, name), encoding="utf-8") as f:
                    texts[name[:-4]] = f.read().strip()
        metadata[locale] = texts
    return metadata


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


def display_type(size):
    for display, sizes in DISPLAYS.items():
        if size in sizes or (size[1], size[0]) in sizes:
            return display
    return None


def read_screenshots(folder):
    """{locale: {display type: [paths in upload order]}}"""
    shots = {}
    if not folder:
        return shots
    for locale in sorted(os.listdir(folder)):
        path = os.path.join(folder, locale)
        if not os.path.isdir(path):
            continue
        for name in sorted(os.listdir(path)):
            if not name.endswith(".png"):
                continue
            file = os.path.join(path, name)
            size = png_size(file)
            display = display_type(size) if size else None
            if not display:
                fail(f"{file}: {size} is not a size App Store Connect takes for iPhone 6.9\" or iPad 13\"")
            shots.setdefault(locale, {}).setdefault(display, []).append(file)
    return shots


def check(metadata, shots):
    problems = []
    for locale, texts in metadata.items():
        for field, text in texts.items():
            if field not in FIELDS:
                problems.append(f"{locale}: {field}.txt is not a field this script knows ({', '.join(FIELDS)})")
                continue
            limit = FIELDS[field][2]
            if limit and len(text) > limit:
                problems.append(f"{locale}: {field} has {len(text)} characters, the limit is {limit}")
            if field.endswith("_url") and not text.startswith("https://"):
                problems.append(f"{locale}: {field} is not an https URL")
        keywords = texts.get("keywords", "")
        if any(k != k.strip() for k in keywords.split(",")):
            problems.append(f"{locale}: keywords have spaces around the commas, which count against the limit")
    for locale, displays in shots.items():
        for display, files in displays.items():
            if len(files) > MAX_SCREENSHOTS:
                problems.append(f"{locale}/{display}: {len(files)} screenshots, the limit is {MAX_SCREENSHOTS}")
    for problem in problems:
        print(f"::error::{problem}")
    if problems:
        sys.exit(1)
    for locale, texts in metadata.items():
        log(f"{locale}: {', '.join(texts) or 'no texts'}")
    for locale, displays in shots.items():
        log(f"{locale} screenshots: " + ", ".join(f"{len(f)} x {d}" for d, f in displays.items()))


#App Store Connect side

class Api:
    def __init__(self, key_id, issuer_id, key_p8):
        self.key_id, self.issuer_id, self.key_p8 = key_id, issuer_id, key_p8
        self.token, self.token_time = None, 0

    def _token(self):
        #Tokens may live 20 minutes; a fresh one every 10 keeps a long upload clear of the limit
        if self.token and time.time() - self.token_time < 600:
            return self.token
        import jwt
        now = int(time.time())
        self.token = jwt.encode(
            {"iss": self.issuer_id, "iat": now, "exp": now + 1200, "aud": "appstoreconnect-v1"},
            self.key_p8, algorithm="ES256", headers={"kid": self.key_id, "typ": "JWT"})
        self.token_time = now
        return self.token

    def request(self, method, path, body=None, params=None, allow_404=False):
        url = path if path.startswith("https://") else API + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data = json.dumps(body).encode() if body is not None else None
        for attempt in range(4):
            req = urllib.request.Request(url, data=data, method=method, headers={
                "Authorization": f"Bearer {self._token()}",
                "Content-Type": "application/json",
            })
            try:
                with urllib.request.urlopen(req, timeout=120) as response:
                    payload = response.read()
                    return json.loads(payload) if payload else {}
            except urllib.error.HTTPError as error:
                text = error.read().decode(errors="replace")
                if error.code == 404 and allow_404:
                    return None
                if error.code in (429, 500, 502, 503, 504) and attempt < 3:
                    time.sleep(2 ** (attempt + 1))
                    continue
                fail(f"{method} {path} answered {error.code}: {describe_errors(text)}")
            except urllib.error.URLError as error:
                if attempt < 3:
                    time.sleep(2 ** (attempt + 1))
                    continue
                fail(f"{method} {path} failed: {error}")

    def get(self, path, **params):
        return self.request("GET", path, params=params or None)

    def get_all(self, path, **params):
        params.setdefault("limit", 200)
        result = self.get(path, **params)
        items = list(result.get("data", []))
        while result.get("links", {}).get("next"):
            result = self.request("GET", result["links"]["next"])
            items += result.get("data", [])
        return items

    def patch(self, path, body):
        return self.request("PATCH", path, body)

    def post(self, path, body):
        return self.request("POST", path, body)

    def delete(self, path):
        return self.request("DELETE", path)


def describe_errors(text):
    try:
        errors = json.loads(text).get("errors", [])
        return "; ".join(f"{e.get('title', '')}: {e.get('detail', '')}".strip(": ") for e in errors) or text
    except ValueError:
        return text[:500]


def api_from_environment():
    key_id = os.environ.get("ASC_KEY_ID", "").strip()
    issuer_id = os.environ.get("ASC_ISSUER_ID", "").strip()
    key_p8 = os.environ.get("ASC_KEY_P8", "").strip()
    for name, value in [("ASC_KEY_ID", key_id), ("ASC_ISSUER_ID", issuer_id), ("ASC_KEY_P8", key_p8)]:
        if not value:
            fail(f"{name} is not set")
    if not key_p8.startswith("-----BEGIN"):
        import base64
        key_p8 = base64.b64decode(key_p8).decode()
    return Api(key_id, issuer_id, key_p8)


def find_app(api, bundle_id):
    apps = api.get("/v1/apps", **{"filter[bundleId]": bundle_id}).get("data", [])
    if not apps:
        fail(f"No app with the bundle ID {bundle_id} in App Store Connect")
    return apps[0]


def editable_app_info(api, app_id):
    for info in api.get_all(f"/v1/apps/{app_id}/appInfos"):
        state = info["attributes"].get("state") or info["attributes"].get("appStoreState")
        if state not in ("READY_FOR_DISTRIBUTION", "READY_FOR_SALE", "REPLACED_WITH_NEW_INFO"):
            return info
    fail("No editable app information (every one is already live)")


def find_version(api, app_id, version_string):
    for version in api.get_all(f"/v1/apps/{app_id}/appStoreVersions", **{"filter[platform]": "IOS"}):
        attributes = version["attributes"]
        if attributes["versionString"] == version_string:
            return version, attributes.get("appVersionState") or attributes.get("appStoreState")
    fail(f"No version {version_string} in App Store Connect")


def update(api, kind, item, wanted, label):
    """PATCHes the attributes of item that differ from wanted"""
    changed = {k: v for k, v in wanted.items() if item["attributes"].get(k) != v}
    if not changed:
        log(f"  {label}: up to date")
        return
    api.patch(f"/v1/{kind}/{item['id']}", {"data": {"type": kind, "id": item["id"], "attributes": changed}})
    log(f"  {label}: set {', '.join(sorted(changed))}")


def sync_localizations(api, kind, parent_kind, parent_id, metadata):
    """Sets the texts that go into this kind of localization; returns {locale: localization}"""
    existing = {l["attributes"]["locale"]: l for l in api.get_all(f"/v1/{parent_kind}/{parent_id}/{kind}")}
    relationship = {"appInfoLocalizations": "appInfo", "appStoreVersionLocalizations": "appStoreVersion"}[kind]
    for locale, texts in metadata.items():
        wanted = {attribute: texts[field] for field, (resource, attribute, _) in FIELDS.items()
                  if resource == kind and field in texts}
        if locale in existing:
            if wanted:
                update(api, kind, existing[locale], wanted, f"{locale} {kind}")
        else:
            existing[locale] = api.post(f"/v1/{kind}", {"data": {
                "type": kind, "attributes": dict(wanted, locale=locale),
                "relationships": {relationship: {"data": {"type": parent_kind, "id": parent_id}}}}})["data"]
            log(f"  {locale} {kind}: added with {', '.join(sorted(wanted)) or 'no texts'}")
    return existing


def sync_build(api, app_id, version):
    current = api.get(f"/v1/appStoreVersions/{version['id']}/relationships/build").get("data")
    if current:
        build = api.get(f"/v1/builds/{current['id']}")["data"]
        log(f"  build: {build['attributes']['version']}")
        return
    version_string = version["attributes"]["versionString"]
    builds = [b for b in api.get("/v1/builds", **{"filter[app]": app_id, "filter[preReleaseVersion.version]": version_string,
                                                  "sort": "-uploadedDate", "limit": 50}).get("data", [])
              if not b["attributes"].get("expired") and b["attributes"].get("processingState") == "VALID"]
    if not builds:
        fail(f"No processed build of version {version_string}; is the release run finished?")
    api.patch(f"/v1/appStoreVersions/{version['id']}/relationships/build", {"data": {"type": "builds", "id": builds[0]["id"]}})
    log(f"  build: selected {builds[0]['attributes']['version']}")


def md5(path):
    digest = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def upload_screenshot(api, set_id, path):
    shot = api.post("/v1/appScreenshots", {"data": {
        "type": "appScreenshots", "attributes": {"fileName": os.path.basename(path), "fileSize": os.path.getsize(path)},
        "relationships": {"appScreenshotSet": {"data": {"type": "appScreenshotSets", "id": set_id}}}}})["data"]
    with open(path, "rb") as f:
        content = f.read()
    for operation in shot["attributes"]["uploadOperations"]:
        chunk = content[operation["offset"]:operation["offset"] + operation["length"]]
        headers = {h["name"]: h["value"] for h in operation.get("requestHeaders", [])}
        req = urllib.request.Request(operation["url"], data=chunk, method=operation["method"], headers=headers)
        for attempt in range(4):
            try:
                urllib.request.urlopen(req, timeout=300).read()
                break
            except (urllib.error.HTTPError, urllib.error.URLError) as error:
                if attempt == 3:
                    fail(f"Uploading {path} failed: {error}")
                time.sleep(2 ** (attempt + 1))
    api.patch(f"/v1/appScreenshots/{shot['id']}", {"data": {
        "type": "appScreenshots", "id": shot["id"],
        "attributes": {"uploaded": True, "sourceFileChecksum": md5(path)}}})


def sync_screenshots(api, localizations, shots):
    log("Screenshots")
    for locale, displays in shots.items():
        localization = localizations.get(locale)
        if not localization:
            log(f"::warning::Screenshots for {locale}, which App Store Connect does not have; add texts for it first")
            continue
        sets = {s["attributes"]["screenshotDisplayType"]: s
                for s in api.get_all(f"/v1/appStoreVersionLocalizations/{localization['id']}/appScreenshotSets")}
        for display, files in displays.items():
            if display in sets:
                set_id = sets[display]["id"]
            else:
                set_id = api.post("/v1/appScreenshotSets", {"data": {
                    "type": "appScreenshotSets", "attributes": {"screenshotDisplayType": display},
                    "relationships": {"appStoreVersionLocalization": {"data": {
                        "type": "appStoreVersionLocalizations", "id": localization["id"]}}}}})["data"]["id"]
            current = api.get_all(f"/v1/appScreenshotSets/{set_id}/appScreenshots")
            if [s["attributes"].get("sourceFileChecksum") for s in current] == [md5(f) for f in files]:
                log(f"  {locale} {display}: up to date")
                continue
            for shot in current:
                api.delete(f"/v1/appScreenshots/{shot['id']}")
            for path in files:
                upload_screenshot(api, set_id, path)
            log(f"  {locale} {display}: uploaded {len(files)}")
    #Apple processes uploads after the fact; a failed one shows up here rather than at upload time
    time.sleep(10)
    for locale in shots:
        localization = localizations.get(locale)
        if not localization:
            continue
        for shot_set in api.get_all(f"/v1/appStoreVersionLocalizations/{localization['id']}/appScreenshotSets"):
            for shot in api.get_all(f"/v1/appScreenshotSets/{shot_set['id']}/appScreenshots"):
                delivery = shot["attributes"].get("assetDeliveryState") or {}
                if delivery.get("state") == "FAILED":
                    log(f"::warning::{locale} {shot['attributes'].get('fileName')}: Apple could not process it: {delivery.get('errors')}")


def listing(args):
    metadata, settings = read_metadata(), read_app()
    shots = read_screenshots(args.screenshots)
    check(metadata, shots)
    api = api_from_environment()
    app = find_app(api, settings["bundleId"])
    log(f"App: {app['attributes']['name']}, primary language {app['attributes'].get('primaryLocale')}")
    version, state = find_version(api, app["id"], args.version)
    if state not in EDITABLE_VERSION_STATES:
        fail(f"Version {args.version} is {state} and can no longer be edited")

    log("App information")
    info = editable_app_info(api, app["id"])
    sync_localizations(api, "appInfoLocalizations", "appInfos", info["id"], metadata)

    log(f"Version {args.version}")
    update(api, "appStoreVersions", version, {"releaseType": settings["releaseType"]}, "release type")
    sync_build(api, app["id"], version)
    localizations = sync_localizations(api, "appStoreVersionLocalizations", "appStoreVersions", version["id"], metadata)
    if shots:
        sync_screenshots(api, localizations, shots)
    log("Done")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=["check", "listing"])
    parser.add_argument("--version", help="App Store version, like 1.1.0")
    parser.add_argument("--screenshots", help="Folder with <locale>/*.png")
    args = parser.parse_args()
    if args.action == "check":
        check(read_metadata(), read_screenshots(args.screenshots))
        return
    if not args.version:
        parser.error("--version is needed")
    listing(args)


if __name__ == "__main__":
    main()
