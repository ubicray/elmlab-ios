#!/usr/bin/env python3
"""Elm Lab: Azerbaijani for the iOS app, and the Elm Lab texts of the Android fork.
Usage, from the repository root:
    python3 tools/elmlab/import_android_strings.py <checkout of github.com/Abbasovel/phyphox-android, branch elmlab>
- az.lproj/Localizable.strings: every iOS key that Android's values-az has (same key names, the
  phyphox translations are shared), plus the iOS-only keys translated below. Keys missing from both
  fall back to English (localize() in localizationHelper.swift).
- az.lproj/InfoPlist.strings: the permission texts, translated below.
- en, ru, tr and az get the Elm Lab home screen and credits texts from Android (elmlab* keys).
- Android's Azerbaijani terminology fixes (tools/elmlab/az_fixes.py there) are applied.
Idempotent: az.lproj is rewritten, and the Elm Lab block in the other tables is replaced."""
import re, sys, pathlib, xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[2]
APP = ROOT / "phyphox-iOS/phyphox"

#The Elm Lab keys the iOS app uses (the update blocker and the licences toggle are Android only)
ELMLAB = re.compile(r"elmlab(Museum|Attribution|(Demo|Tools|Sensor)Heading|(Demo|Tool|Sensor)\w+(Title|Sub))$")
#Source code of this app, for the attribution text
SOURCE = ("github.com/Abbasovel/phyphox-android", "github.com/ubicray/elmlab-ios")

#az_fixes.py of the Android fork: Azerbaijani terminology agreed during the phyphox translation
AZ_RULES = [
    ("Xam sensorlar", "Sensorlar"),
    ("Xam verilənlər", "Verilənlər"),
    ("xam mövqe verilənlərini", "mövqe verilənlərini"),
    ("xam verilənlər", "verilənlər"),
    ("Xam spektr", "İlkin spektr"),
    ("Giroskop (dönmə sürəti)", "Giroskop (bucaq sürəti)"),
    ("dönmə sürəti", "bucaq sürəti"),
    ("Dönmə sürəti", "Bucaq sürəti"),
    ("aAlətlər", "Alətlər"),
]

#Keys only the iOS app has, so Android's translation has nothing for them
AZ_IOS = {
    "apple_ban": "Bu təcrübə artıq mövcud deyil.",
    "actions": "Əməliyyatlar",
    "cameraNotAvailableWarningText": "Bu təcrübə mövcud deyil, çünki cihazınızın iOS versiyası kamera ilə analiz üçün tələb olunan minimum versiyadan köhnədir.",
    "cameraLoadingErrorTitle": "Kameranın yüklənməsində xəta",
    "cameraLoadingErrorMessage1": "Kameranı tənzimləmək mümkün olmadı. ",
    "cameraLoadingErrorMessage2": "Standart video cihazı əlçatan deyil. ",
    "cameraLoadingErrorMessage3": "Video cihazının girişini kamera sessiyasına əlavə etmək mümkün olmadı. ",
    "cameraLoadingErrorMessage4": "Çıxışı kamera sessiyasına əlavə etmək mümkün deyil. ",
    "cameraLoadingErrorMessage5": "Video cihazının girişini yaratmaq mümkün olmadı. ",
    "cameraLoadingErrorMessage6": "Kamera düzgün yüklənə bilmədi. ",
    "cameraLoadingErrorSecondMessage": "Zəhmət olmasa təcrübəni yenidən açın.",
    "cameraConfigErrorMessage": "Kameranı tənzimləmək alınmadı. Ya cihazınızın kamerası əlçatan deyil, ya da ona icazə verilməyib.",
    "appleBanWarningMoreInfo": "Ətraflı",
    "accept": "Qəbul et",
    "select": "--seçin--",
    "chooseOption": "Variant seçin",
    "disableTimedRun": "Vaxtlı ölçməni söndür",
    "switch_to_calibrated_magnetometer": "Kalibrlənmiş maqnitometrə keç",
    "switch_to_raw_magnetometer": "Emal olunmamış maqnitometrə keç",
    "enableRemoteServer": "Uzaqdan girişi aktivləşdir",
    "disableRemoteServer": "Uzaqdan girişi söndür",
    "url_invalid": "Yanlış URL",
    "url_invalid_msg": "Bu təcrübə sadəcə keçiddir, lakin etibarlı URL tapılmadı.",
    "AudioRateMissmatch": "Xəta: səsin diskretləşdirmə tezliyi uyğun gəlmir. Zəhmət olmasa başqa tezlik tətbiq edən proqram və xidmətləri (məsələn, AirPlay) söndürün.",
    "remoteCameraWarning": "Kameranın uzaq interfeysdə önizlənməsi və idarə edilməsi dəstəklənmir.",
    "showQRCodeForRemoteURL": "Ünvana daxil olmaq üçün QR kod",
    "notSet": "Təyin edilməyib",
    "preview": "Önizləmə",
    "permission_microphone_required": "Mikrofon lazımdır",
    "permission_microphone_denied": "Bu təcrübə üçün mikrofona giriş lazımdır, lakin giriş rədd edilib. Zəhmət olmasa Tənzimləmələr->Məxfilik->Mikrofon bölməsində girişə icazə verin.",
    "permission_microphone_restricted": "Bu təcrübə üçün mikrofona giriş lazımdır, lakin giriş məhdudlaşdırılıb. Zəhmət olmasa Tənzimləmələr->Ekran vaxtı->Məhdudiyyətlər->Mikrofon bölməsində girişə icazə verin.",
    "permission_location_required": "Məkan/GPS lazımdır",
    "permission_location_denied": "Bu təcrübə üçün məkana (GPS) giriş lazımdır, lakin giriş rədd edilib. Zəhmət olmasa Tənzimləmələr->Məxfilik->Məkan xidmətləri bölməsində girişə icazə verin.",
    "permission_location_restricted": "Bu təcrübə üçün məkana (GPS) giriş lazımdır, lakin giriş məhdudlaşdırılıb. Zəhmət olmasa Tənzimləmələr->Ekran vaxtı->Məhdudiyyətlər->Məkan xidmətləri bölməsində girişə icazə verin.",
    "permission_motion_required": "Hərəkət və fitnes icazəsi lazımdır",
    "permission_motion_denied": "Bu təcrübə üçün hərəkət verilənlərinə giriş lazımdır, lakin giriş rədd edilib. Zəhmət olmasa Tənzimləmələr->Məxfilik->Hərəkət və fitnes bölməsində icazəni aktivləşdirin.",
    "permission_motion_restricted": "Bu təcrübə üçün hərəkət verilənlərinə giriş lazımdır, lakin giriş məhdudlaşdırılıb. Zəhmət olmasa Tənzimləmələr->Məxfilik->Hərəkət və fitnes bölməsində icazəni aktivləşdirin.",
    "permission_camera_required": "Kamera lazımdır",
    "permission_camera_denied": "Bu təcrübə üçün kameraya giriş lazımdır, lakin giriş rədd edilib. Zəhmət olmasa Tənzimləmələr->Məxfilik->Kamera bölməsində girişə icazə verin.",
    "permission_camera_restricted": "Bu təcrübə üçün kameraya giriş lazımdır, lakin giriş məhdudlaşdırılıb. Zəhmət olmasa Tənzimləmələr->Ekran vaxtı->Məhdudiyyətlər->İcazə verilən funksiyalar->Kamera bölməsində girişə icazə verin.",
    "rangeSliderLowerValue": "Aşağı dəyər",
    "rangeSliderUpperValue": "Yuxarı dəyər",
}

AZ_INFOPLIST = {
    "NSMicrophoneUsageDescription": "Elm Lab mikrofondan səsi digər sensorlar kimi qeydə alır və seçilmiş təcrübəyə uyğun analiz edir. Verilənlər yalnız istifadəçi xaricə köçürmə funksiyası ilə bunu seçdikdə tətbiqdən çıxarılır.",
    "NSLocalNetworkUsageDescription": "Elm Lab yerli şəbəkənizə bu hallarda daxil olur: təcrübə konfiqurasiyası şəbəkənizdəki cihazdan yükləndikdə, təcrübə yerli cihazlardan (məsələn, Wi-Fi ölçmə avadanlığı və ya MQTT brokeri) verilənləri oxuduqda və ya onlara göndərdikdə, və təcrübəni veb brauzerdən idarə etmək üçün uzaqdan giriş aktivləşdirildikdə.",
    "NSLocationWhenInUseUsageDescription": "Elm Lab GPS-dən məkan verilənlərini digər sensorlar kimi qeydə alır və seçilmiş təcrübəyə uyğun analiz edir. Verilənlər yalnız istifadəçi xaricə köçürmə funksiyası ilə bunu seçdikdə tətbiqdən çıxarılır.",
    "NSPhotoLibraryAddUsageDescription": "Təcrübə menyusunda «Ekran görüntüsünü paylaş» seçdikdə Elm Lab ekran görüntülərini foto kitabxananıza əlavə edə bilər.",
    "NSMotionUsageDescription": "Elm Lab fizika təcrübələrində istifadə etmək üçün telefonunuzun sensorlarını oxuyur.",
    "NSCameraUsageDescription": "Elm Lab xüsusi təcrübə konfiqurasiyalarını əlavə etmək üçün QR kodları kamera ilə skan edir. Kamera həmçinin optik təcrübələrdə və dərinlik sensoru (LiDAR/ToF) ilə təcrübələrdə ölçmə aləti kimi istifadə olunur.",
    "NSBluetoothPeripheralUsageDescription": "Elm Lab xarici Bluetooth sensorlarından verilənləri oxuya və xarici Bluetooth cihazlarına verilənlər göndərə bilir.",
    "NSBluetoothAlwaysUsageDescription": "Elm Lab xarici Bluetooth sensorlarından verilənləri oxuya və xarici Bluetooth cihazlarına verilənlər göndərə bilir.",
}

ENTRY = re.compile(r'^"([^"]+)"\s*=\s*"((?:[^"\\]|\\.)*)";', re.M)
BEGIN, END = "/* Elm Lab (tools/elmlab/import_android_strings.py) */", "/* End Elm Lab */"

def android(res, folder):
    """Android string resources as plain text: whitespace collapsed, escapes resolved"""
    strings = {}
    for e in ET.parse(res / folder / "strings.xml").getroot():
        if e.tag != "string" or e.get("translatable") == "false": continue
        s = re.sub(r"\s+", " ", "".join(e.itertext())).strip()
        if len(s) >= 2 and s[0] == s[-1] == '"': s = s[1:-1]
        s = re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), s)
        strings[e.get("name")] = re.sub(r" *\n *", "\n", s)
    return strings

def quote(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")

def unquote(s):
    return re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), s)

def az_fix(s):
    for a, b in AZ_RULES: s = s.replace(a, b)
    return s

def elmlab_block(strings):
    lines = [f'"{k}" = "{quote(v.replace(*SOURCE))}";' for k, v in strings.items() if ELMLAB.match(k)]
    return "\n".join([BEGIN] + lines + [END]) + "\n"

def with_elmlab(text, strings):
    text = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n", "", text, flags=re.S)
    return text.rstrip("\n") + "\n\n" + elmlab_block(strings)

HEADER = "/*\n  {name}\n  Elm Lab, Azerbaijani. Generated by tools/elmlab/import_android_strings.py\n*/\n"

def main(res):
    en_text = (APP / "en.lproj/Localizable.strings").read_text(encoding="utf-8")
    en = {k: unquote(v) for k, v in ENTRY.findall(en_text)}
    az = {k: az_fix(v) for k, v in android(res, "values-az").items()}

    out, missing = [], []
    for key, english in en.items():
        if ELMLAB.match(key): continue
        if key in AZ_IOS: value = AZ_IOS[key]
        elif key in az and not key.endswith(("URL", "_url")): value = az[key]
        else: missing.append(key); continue
        if "%" not in english: value = re.sub(r"\s*%\d\$s", "", value) #Android appends the URL itself
        out.append(f'"{key}" = "{quote(value)}";')
    d = APP / "az.lproj"; d.mkdir(exist_ok=True)
    (d / "Localizable.strings").write_text(HEADER.format(name="Localizable.strings") + "\n".join(out) + "\n\n" + elmlab_block(az), encoding="utf-8")
    (d / "InfoPlist.strings").write_text(HEADER.format(name="InfoPlist.strings") + "\n".join(f'"{k}" = "{quote(v)}";' for k, v in AZ_INFOPLIST.items()) + "\n", encoding="utf-8")
    print(f"az: {len(out)} of {len([k for k in en if not ELMLAB.match(k)])} keys, English fallback for {missing}")

    for lang, folder in (("en", "values"), ("ru", "values-ru"), ("tr", "values-tr")):
        p = APP / f"{lang}.lproj/Localizable.strings"
        p.write_text(with_elmlab(p.read_text(encoding="utf-8"), android(res, folder)), encoding="utf-8")
    print("Elm Lab texts added to en, ru, tr and az")

if __name__ == "__main__":
    main(pathlib.Path(sys.argv[1]) / "app/src/main/res")
