#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
: "${AI_UI_SIMULATOR_UDID:?Select a dedicated test Simulator first}"
DERIVED_DATA_PATH="${AI_UI_DERIVED_DATA_PATH:-$ROOT_DIR/.derivedData/ai-ui}"

for file in ExternalDeveloper LocalOverrides; do
  destination="iOS/Configuration/$file.xcconfig"
  if [[ "$file" == "LocalOverrides" ]]; then destination="iOS/$file.xcconfig"; fi
  if [[ ! -f "$destination" ]]; then
    cp ".github/ai-ui/$file.xcconfig" "$destination"
  fi
done

export SKIP_STRINGS=1
xcodebuild build-for-testing \
  -project iOS/DuckDuckGo-iOS.xcodeproj -scheme 'iOS UI Tests' -configuration Debug \
  -testPlan 'UI Tests' \
  '-only-testing:UI Tests/KeyboardSettingsUITests/testKeyboardPreferencesPersistAfterReopeningAndRelaunching' \
  -destination "platform=iOS Simulator,id=$AI_UI_SIMULATOR_UDID,arch=$(uname -m)" \
  -derivedDataPath "$DERIVED_DATA_PATH" \
  -disableAutomaticPackageResolution -onlyUsePackageVersionsFromResolvedFile \
  -packageAuthorizationProvider netrc -skipMacroValidation -jobs 2 -parallel-testing-enabled NO \
  CODE_SIGNING_ALLOWED=YES CODE_SIGNING_REQUIRED=YES CODE_SIGN_IDENTITY=- \
  CODE_SIGN_STYLE=Manual DEVELOPMENT_TEAM= PROVISIONING_PROFILE_SPECIFIER= \
  COMPILER_INDEX_STORE_ENABLE=NO
