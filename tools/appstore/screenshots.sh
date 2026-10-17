#!/bin/bash
# App Store screenshots of Elm Lab, taken in a simulator (macOS only).
#
#   screenshots.sh APP OUTPUT DEVICE LANGUAGE LOCALE...
#
# APP is the built simulator .app, DEVICE "ipad" (iPad Pro 13-inch) or "iphone" (the newest
# Pro Max), LANGUAGE the app's language in the screenshots (az, en, ...), and LOCALE an App Store
# Connect locale such as en-US. The same screenshots go to every LOCALE, as
# OUTPUT/<locale>/<device>-<n>-<name>.png at the device's native size, which is what App Store Connect takes
# for that set:
#
#   1-home           the home screen
#   2-acceleration   acceleration with g, a phone bouncing on a spring
#   3-gyroscope      the gyroscope, a phone swinging as a pendulum
#
# The two measurements are saved states made by make_states.py, because the simulator has no
# motion sensors. The app is driven with its launch arguments only (see AutomationLaunchOptions in
# AppDelegate.swift), so no UI test is involved.
set -euo pipefail

APP="$1"; OUTPUT="$2"; DEVICE="$3"; LANGUAGE="$4"; shift 4
HERE="$(cd "$(dirname "$0")" && pwd)"
BUNDLE_ID="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$APP/Info.plist")"

case "$DEVICE" in
  ipad) PATTERN='iPad Pro 13-inch' ;;
  iphone) PATTERN='Pro Max' ;;
  *) echo "DEVICE is ipad or iphone" >&2; exit 1 ;;
esac
UDID=$(xcrun simctl list devices available -j | PATTERN="$PATTERN" python3 -c "
import json, os, sys
devices = json.load(sys.stdin)['devices']
found = [d for runtime in sorted(devices) if 'iOS' in runtime for d in devices[runtime] if os.environ['PATTERN'] in d['name']]
print(found[-1]['udid'] if found else '')")
if [ -z "$UDID" ]; then
  echo "No '$PATTERN' simulator on this runner" >&2
  xcrun simctl list devices available >&2
  exit 1
fi
echo "Simulator: $(xcrun simctl list devices | grep "$UDID")"

xcrun simctl boot "$UDID" 2>/dev/null || true
xcrun simctl bootstatus "$UDID" -b
xcrun simctl ui "$UDID" appearance dark
xcrun simctl status_bar "$UDID" override --time 9:41 --dataNetwork wifi --wifiMode active --wifiBars 3 \
  --cellularMode active --cellularBars 4 --batteryState charged --batteryLevel 100
xcrun simctl install "$UDID" "$APP"

STATES="$(mktemp -d)"
python3 "$HERE/make_states.py" "$STATES"
# In the app's own Documents folder the states open in place, as the app's saved states do
DOCUMENTS="$(xcrun simctl get_app_container "$UDID" "$BUNDLE_ID" data)/Documents"
mkdir -p "$DOCUMENTS"
cp "$STATES"/*.phyphox "$DOCUMENTS/"

SHOTS="$(mktemp -d)"
shoot() {
  local name="$1"; shift
  local region; region="$(echo "$LANGUAGE" | tr '[:lower:]' '[:upper:]')"
  xcrun simctl terminate "$UDID" "$BUNDLE_ID" 2>/dev/null || true
xcrun simctl shutdown "$UDID"
  # The damage warning on the home screen and the hint bubbles on an experiment are for first-time
  # users and would cover the screenshot
  xcrun simctl launch "$UDID" "$BUNDLE_ID" \
    -AppleLanguages "($LANGUAGE)" -AppleLocale "${LANGUAGE}_$region" \
    -donotshowagain YES -experiment_start_hint_dismiss_count 3 -experiment_info_hint_dismiss_count 3 \
    "$@" >/dev/null
  sleep 8
  xcrun simctl io "$UDID" screenshot --type=png "$SHOTS/$name.png" >/dev/null
  echo "$name.png"
}

shoot 1-home
shoot 2-acceleration -phyphoxAutoConfirm -phyphoxUrl "file://$DOCUMENTS/accelerometer.phyphox"
shoot 3-gyroscope -phyphoxAutoConfirm -phyphoxUrl "file://$DOCUMENTS/gyroscope.phyphox"
for locale in "$@"; do
  mkdir -p "$OUTPUT/$locale"
  for shot in "$SHOTS"/*.png; do
    cp "$shot" "$OUTPUT/$locale/$DEVICE-$(basename "$shot")"
  done
done

xcrun simctl terminate "$UDID" "$BUNDLE_ID" 2>/dev/null || true
xcrun simctl shutdown "$UDID"
