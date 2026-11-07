---
summary: Use a labelled one-line storage fault to verify the existing UI assertion without claiming an upstream or model-generated regression.
read_when:
  - Changing the controlled proof workflow or its seeded mutation
  - Interpreting a deliberately failing native test as showcase evidence
---

# Controlled native proof

Date: 2026-11-07. Status: Accepted.

## Context and constraints

The independent showcase review found meaningful native baseline passes but no
demonstrated failure sensitivity. No provider API secret is configured. The owner
approved concentrating active work on DuckDuckGo and implementing the review's
recommendations. Successful baseline execution and live release-test generation
must remain distinct claims.

## Decision

Use the existing upstream keyboard-preference UI test and the already verified
source snapshot. In an isolated manual CI job, first run the correct app, then
alias App Launch to New Tab's storage key, then restore the original source and
run again. Keep the assertion and fixture unchanged. Require native pass-fail-pass
counts, an equality-assertion failure, unchanged test source and byte-identical
restoration. Publish evidence only after all conditions pass, using a separate
write-enabled job. Record the fault as seeded in every summary.

## Alternatives

- Treating an ordinary green baseline as regression evidence: rejected because
  it does not establish whether the assertion catches a relevant fault.
- Altering the test assertion to force a failure: rejected because it would not
  demonstrate detection of an application defect.
- Calling this live generated release coverage: rejected because the fixed
  baseline bypasses the provider planner and uses an inspected branch snapshot.
- Waiting for credentials before any further evidence: rejected because native
  failure sensitivity can be verified independently without API usage.

## Consequences

The workflow intentionally includes one failing native execution and multiple
incremental builds. That expected failure counts as evidence only when the same
test passes before and after correction. This adds a stronger public baseline
demonstration; it does not establish unattended generation, a real upstream
regression, or easy onboarding for an independent new user.
