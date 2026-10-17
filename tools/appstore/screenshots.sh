#!/bin/bash
# App Store screenshots of Elm Lab, taken in a simulator (macOS only).
#
#   screenshots.sh APP OUTPUT DEVICE LOCALE...
#
# APP is the built simulator .app, DEVICE "ipad" (iPad Pro 13-inch) or "iphone" (the newest
# Pro Max), LOCALE an App Store Connect locale such as en-US. Writes OUTPUT/<locale>/<n>-<name>.png
# at the device's native size, which is what App Store Connect takes for that set:
#
#   1-home           the home screen
#   2-acceleration   acceleration with g, a phone bouncing on a spring
#   3-gyroscope      the gyroscope, a phone swinging as a pendulum
#
# The two measurements are saved states made by make_states.py, because the simulator has no
# motion sensors. The app is driven with its launch arguments only (see AutomationLaunchOptions in
# AppDelegate.swift), so no UI test is involved.
set -euo pipefail

APP="$1"; OUTPUT="$2"; DEVICE="$3"; shift 3
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

shoot() {
  local locale="$1" name="$2"; shift 2
  local language="${locale%%-*}" region="${locale#*-}"
  [ "$region" = "$locale" ] && region="$(echo "$language" | tr '[:lower:]' '[:upper:]')"
  xcrun simctl terminate "$UDID" "$BUNDLE_ID" 2>/dev/null || true
  # The damage warning on the home screen and the hint bubbles on an experiment are for first-time
  # users and would cover the screenshot
  xcrun simctl launch "$UDID" "$BUNDLE_ID" \
    -AppleLanguages "($language)" -AppleLocale "${language}_$region" \
    -donotshowagain YES -experiment_start_hint_dismiss_count 3 -experiment_info_hint_dismiss_count 3 \
    "$@" >/dev/null
  sleep 8
  mkdir -p "$OUTPUT/$locale"
  xcrun simctl io "$UDID" screenshot --type=png "$OUTPUT/$locale/$name.png" >/dev/null
  echo "$locale/$name.png"
}

for locale in "$@"; do
  shoot "$locale" 1-home
  shoot "$locale" 2-acceleration -phyphoxAutoConfirm -phyphoxUrl "file://$DOCUMENTS/accelerometer.phyphox"
  shoot "$locale" 3-gyroscope -phyphoxAutoConfirm -phyphoxUrl "file://$DOCUMENTS/gyroscope.phyphox"
done

xcrun simctl terminate "$UDID" "$BUNDLE_ID" 2>/dev/null || true
