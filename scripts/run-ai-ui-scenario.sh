#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
if [[ "${1:-}" == "inspect" ]]; then
  echo "This example maps one reviewed scenario to an existing native XCTest; AI inspection/planning is not configured." >&2
  exit 2
fi
if [[ "${1:-}" == "run" ]]; then shift; fi
SCENARIO_PATH="${AI_UI_SCENARIO_PATH:-${1:-$ROOT_DIR/.github/ai-ui/verify-primary-flow.json}}"
ARTIFACTS_DIR="${AI_UI_ARTIFACTS_DIR:-$ROOT_DIR/artifacts/ai-ui/$(date +%Y%m%d-%H%M%S)}"
DERIVED_DATA_PATH="${AI_UI_DERIVED_DATA_PATH:-$ROOT_DIR/.derivedData/ai-ui}"
: "${AI_UI_SIMULATOR_UDID:?Select a dedicated test Simulator first}"

# The native test owns launch fixtures, switch-value assertions and relaunch persistence.
python3 - "$SCENARIO_PATH" <<'PY'
import json
from pathlib import Path
import sys

scenario = json.loads(Path(sys.argv[1]).read_text())
expected_steps = [{"action": "launch"}, {"action": "assertVisible", "label": "Keyboard"}]
if scenario.get("steps") != expected_steps:
    raise SystemExit("Unsupported scenario: this runner implements only the reviewed native keyboard-preference flow")
PY

mkdir -p "$ARTIFACTS_DIR"
RESULT_PATH="$ARTIFACTS_DIR/DuckDuckGoUITests.xcresult"
if [[ -e "$RESULT_PATH" ]]; then
  echo "Result bundle already exists; use a fresh AI_UI_ARTIFACTS_DIR to preserve evidence." >&2
  exit 2
fi

export SKIP_STRINGS=1
set +e
xcodebuild test-without-building \
  -project iOS/DuckDuckGo-iOS.xcodeproj -scheme 'iOS UI Tests' -configuration Debug \
  -testPlan 'UI Tests' \
  '-only-testing:UI Tests/KeyboardSettingsUITests/testKeyboardPreferencesPersistAfterReopeningAndRelaunching' \
  -destination "platform=iOS Simulator,id=$AI_UI_SIMULATOR_UDID,arch=$(uname -m)" \
  -derivedDataPath "$DERIVED_DATA_PATH" -resultBundlePath "$RESULT_PATH" \
  -disableAutomaticPackageResolution -onlyUsePackageVersionsFromResolvedFile \
  -packageAuthorizationProvider netrc -skipMacroValidation -parallel-testing-enabled NO \
  CODE_SIGNING_ALLOWED=YES CODE_SIGNING_REQUIRED=YES CODE_SIGN_IDENTITY=- CODE_SIGN_STYLE=Manual \
  DEVELOPMENT_TEAM= PROVISIONING_PROFILE_SPECIFIER= COMPILER_INDEX_STORE_ENABLE=NO \
  2>&1 | tee "$ARTIFACTS_DIR/xcodebuild-ui-test.log"
TEST_EXIT="${PIPESTATUS[0]}"
xcrun xcresulttool get test-results summary --path "$RESULT_PATH" --format json \
  > "$ARTIFACTS_DIR/test-results.json" 2> "$ARTIFACTS_DIR/result-summary-error.log"
SUMMARY_EXIT="$?"
set -e

python3 - "$ARTIFACTS_DIR" "$TEST_EXIT" "$SUMMARY_EXIT" <<'PY'
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
result = {}
if sys.argv[3] == "0":
    result = json.loads((root / "test-results.json").read_text())
passed = (sys.argv[2] == "0" and result.get("totalTestCount") == 1
          and result.get("passedTests") == 1 and result.get("failedTests") == 0
          and result.get("skippedTests") == 0)
status = "passed" if passed else "failed"
(root / "summary.md").write_text(
    "## DuckDuckGo native UI check\n\n"
    f"- Result: {status}\n"
    "- XCTest: UI Tests/KeyboardSettingsUITests/testKeyboardPreferencesPersistAfterReopeningAndRelaunching\n"
    f"- Tests: {result.get('totalTestCount', 'unavailable')}; "
    f"passed: {result.get('passedTests', 'unavailable')}; "
    f"failed: {result.get('failedTests', 'unavailable')}; "
    f"skipped: {result.get('skippedTests', 'unavailable')}\n"
    "- Result bundle: DuckDuckGoUITests.xcresult\n"
    "- Log: xcodebuild-ui-test.log\n\n"
    "Coverage: deterministic launch, real keyboard switches and "
    "preference persistence after navigation and relaunch. This baseline does not establish release-wide "
    "coverage or live model planning. Exactly one passing, unskipped test is required.\n"
)
raise SystemExit(0 if passed else 1)
PY
