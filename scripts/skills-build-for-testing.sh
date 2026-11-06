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
  -testPlan "${AI_UI_TEST_PLAN:-UI Tests}" \
  "-only-testing:${AI_UI_TEST_SELECTOR:-UI Tests/KeyboardSettingsUITests/testKeyboardPreferencesPersistAfterReopeningAndRelaunching}" \
  -destination "platform=iOS Simulator,id=$AI_UI_SIMULATOR_UDID,arch=$(uname -m)" \
  -derivedDataPath "$DERIVED_DATA_PATH" \
  -disableAutomaticPackageResolution -onlyUsePackageVersionsFromResolvedFile \
  -packageAuthorizationProvider netrc -skipMacroValidation -jobs 2 -parallel-testing-enabled NO \
  CODE_SIGNING_ALLOWED=YES CODE_SIGNING_REQUIRED=YES CODE_SIGN_IDENTITY=- \
  CODE_SIGN_STYLE=Manual DEVELOPMENT_TEAM= PROVISIONING_PROFILE_SPECIFIER= \
  COMPILER_INDEX_STORE_ENABLE=NO

# Include extensions copied by shell phases, which Xcode may not validate at build time.
python3 - "$DERIVED_DATA_PATH/Build/Products/Debug-iphonesimulator/DuckDuckGo.app" <<'PYTHON'
import json
from pathlib import Path
import plistlib
import sys

app = Path(sys.argv[1])
def bundle_id(bundle):
    with (bundle / "Info.plist").open("rb") as source:
        return plistlib.load(source)["CFBundleIdentifier"]

parent = bundle_id(app)
extensions = {extension.name: bundle_id(extension)
              for extension in sorted((app / "PlugIns").glob("*.appex"))}
for name, identifier in extensions.items():
    if not identifier.startswith(parent + "."):
        raise SystemExit(f"Embedded extension {name}: {identifier} is outside parent {parent}")
print(json.dumps({"app_bundle_id": parent, "embedded_extension_ids": extensions}, indent=2))
PYTHON
