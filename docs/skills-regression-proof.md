---
summary: Reproduce the controlled native keyboard-preference fault and distinguish it from live generated release coverage.
read_when:
  - Running the flagship's controlled regression proof
  - Reviewing whether the UI test detects a relevant preference-storage failure
---

# Controlled keyboard-preference proof

This manual workflow runs the same unchanged native UI test against the original
app, an explicitly seeded preference-key defect, and restored original source.
It demonstrates assertion sensitivity, independently of model planning.

The source is the inspected snapshot
`838a682e32d0e300c921aae4bf8cf02a203ea5bc`; it is not presented as a new released
version. The existing test verifies both keyboard-preference defaults, independent
changes, navigation, relaunch persistence and restoration. The seeded defect
makes App Launch incorrectly use New Tab's storage key. This is deliberately
introduced test evidence, not a claim that DuckDuckGo shipped that bug.

## Run from a fresh checkout

1. Fork or check out `skills-showcase` and retain its source/harness identities.
2. Open Actions → **Controlled keyboard regression proof** → **Run workflow**.
3. The fresh Xcode 27.1 runner prepares the public build, builds the real app and
   executes UI Check on an iPhone 18 Pro running iOS 27.0. No planner key is used.
4. Inspect `report.json`, logs, video and all three native result bundles.

The workflow must observe one passing, unskipped test before mutation, one failing
native equality assertion with the mutation, and one passing, unskipped test
after restoring byte-identical source. An unexpected pass, skip, build failure,
crash or changed test assertion cannot satisfy the verifier. Source and patch
hashes, action/harness commits and the original test identity are retained.

The native job has read-only repository access. A separate publisher archives
verified evidence under an immutable `skills-controlled-proof-<run>-<attempt>`
prerelease. These are engineering results, not upstream application releases.
Ordinary diagnostic artifacts remain available even if the proof fails.

Status: [run 42372200480](https://github.com/Kofiloski/apple-browsers/actions/runs/42372200480)
passed. Native result bundles independently verify one original pass, one seeded
failure (`XCTAssertEqual`: observed 1, expected 0), and one restored pass, with
zero skips. Original and restored source hashes match. The unchanged test-source
check passed. [Permanent evidence and recordings](https://github.com/Kofiloski/apple-browsers/releases/tag/skills-controlled-proof-42372200480-1)
retain the source/harness/action identities and the exact mutation.

The native run reproduced this from a fresh GitHub-hosted checkout. That is cold
CI reproducibility, not a measured fresh-user onboarding study. Live unattended
diff-driven generation remains unverified because no planner key is configured.

The observed initial cold build took 32 minutes 51 seconds; the complete native
job, including all three variants, took 59 minutes 10 seconds. The manual proof
now allows 75 minutes so a repeat is not constrained by the original 60-minute
limit. This three-variant workload is not scheduled on each upstream release.
Peak disk consumption and a new user's setup time were not measured.
