---
summary: Reproduce the independent DuckDuckGo keyboard-preference UI check and interpret its evidence.
read_when:
  - Running the public iOS skills workflow
  - Reviewing local versus hosted DuckDuckGo test results
---

# Independent DuckDuckGo skills example

This is an independent testing fork preserving DuckDuckGo's source, Apache 2.0
license and attribution. It is not endorsed by DuckDuckGo. App source is pinned
to `838a682e32d0e300c921aae4bf8cf02a203ea5bc`, an inspected branch snapshot. No
released comparison pair has been selected for this example.

The existing
`UI Tests/KeyboardSettingsUITests/testKeyboardPreferencesPersistAfterReopeningAndRelaunching`
test arranges onboarding and its feature flag explicitly, checks both keyboard
defaults, changes them, verifies persistence through navigation and relaunch,
and restores them. It uses the real settings UI and persistence implementation.
No account, model API key or external UI inspector is required.

The fixed native runner accepts only its reviewed scenario and requires exactly
one passing, unskipped test in the XCTest result bundle. AI planning/inspection
is not configured for this native-test mapping.

## Reproduce

Use Xcode 27.1 and a dedicated iPhone Simulator on iOS 27.0. Set `DEVELOPER_DIR`,
`AI_UI_SIMULATOR_UDID`, and optionally `AI_UI_DERIVED_DATA_PATH`. The test clears
this app's defaults, so use an isolated test Simulator.

```bash
bash scripts/skills-build-for-testing.sh
bash scripts/run-ai-ui-scenario.sh .github/ai-ui/verify-primary-flow.json
```

The build helper supplies example external-developer configuration only when
local files are absent, uses a separate test bundle/group identity, and signs
for Simulator ad hoc. It preserves the upstream `UI Tests` scheme and test plan.
`SKIP_STRINGS=1` uses the checked-in translations without rewriting them during
this check. The pinned AppleToolbox URL macro was reviewed before command-local
authorization; global trust settings are unchanged.

The private DuckSansFont package and its single lockfile pin are removed using
the upstream README's supported external-contributor fallback. The app renders
system fonts, so these images are a different visual baseline from builds using
the proprietary font. No font files are copied or distributed by this example.
Other dependency pins and the production Swift/test implementations are unchanged.
The Debug Autofill and Network extensions have Simulator-only bundle IDs derived
from `APP_ID`, preserving their device IDs. The helper validates every embedded
`.appex` ID after building, including the Network extension copied by a shell
phase rather than Xcode's normal embedding phase.

The selected UI path does not use the snapshot-reference or privacy-reference
submodule test corpora. They are not fetched for this example.

## Evidence status

The [hosted run on November 6, 2026](https://github.com/Kofiloski/apple-browsers/actions/runs/42212517733)
passed the full build and selected native test: **one test, zero failures, zero
skips**, in 181.367 seconds. The tested harness is
`83a160b2efb2f237cfc78e04276ae504385de5fc`. Downloaded XCTest results were
independently checked with `xcresulttool`; the runner and native counts match.
The log confirms real navigation, switch changes, termination and relaunch.
Three native screenshots show defaults, changed values and persistence after
relaunch; the workflow also records video. The parent artifact
`duckduckgo-public-check` is retained for 14 days.

Locked dependency resolution passed locally. Both local app-build attempts
stopped at the disk monitor's 1 GiB reserve, including the replay after an
approved Firefox build cleanup. Neither reported a compiler error. A local
DuckDuckGo UI pass is still unverified; the hosted pass is separate evidence.

The [first hosted build](https://github.com/Kofiloski/apple-browsers/actions/runs/42135371081)
failed embedded-binary validation because the Autofill extension retained its
upstream ID under our isolated app ID. The
[next build](https://github.com/Kofiloski/apple-browsers/actions/runs/42139753254)
passed, then Simulator installation found the same mismatch in the Network
extension copied by a shell phase. Both Debug Simulator IDs now derive from
`APP_ID`. All five IDs were verified through Xcode settings and in the completed
app before the passing UI replay. These were integration configuration failures;
production Swift and native test assertions were unchanged.

Retain logs, video, the native screenshots inside `.xcresult`, machine-readable
test counts and source provenance. This check covers keyboard-preference
persistence, not all browser behavior, release-wide changes or live model
planning. The public workflow is manual; inherited upstream release, issue and
notification workflows are disabled on the showcase fork.
