#!/usr/bin/env python3
"""Verify native success, a detected seeded fault, and success after restoration."""
import json
import os
from pathlib import Path
import re


def verify(root, outcomes):
    provenance = json.loads((root / 'provenance.json').read_text())
    mutation = json.loads((root / 'mutation.json').read_text())
    for key in ('source_sha', 'harness_sha', 'action_sha'):
        if not re.fullmatch(r'[0-9a-f]{40}', provenance[key]):
            raise ValueError('Missing immutable identity: ' + key)
    for key in ('original_sha256', 'fault_sha256', 'restored_sha256', 'fault_patch_sha256'):
        if not re.fullmatch(r'[0-9a-f]{64}', mutation.get(key, '')):
            raise ValueError('Missing mutation evidence: ' + key)
    if mutation['original_sha256'] != mutation['restored_sha256']:
        raise ValueError('Restored source differs from the original')
    if mutation['original_sha256'] == mutation['fault_sha256']:
        raise ValueError('Seeded fault did not change source')
    cases = []
    for phase, expected_outcome, expected_counts in (
        ('original', 'success', (1, 1, 0, 0)),
        ('seeded-fault', 'failure', (1, 0, 1, 0)),
        ('restored', 'success', (1, 1, 0, 0)),
    ):
        summary = json.loads((root / phase / 'test-results.json').read_text())
        counts = tuple(summary.get(key) for key in ('totalTestCount', 'passedTests', 'failedTests', 'skippedTests'))
        if outcomes.get(phase) != expected_outcome or counts != expected_counts:
            raise ValueError(f'{phase}: expected action={expected_outcome}, native counts={expected_counts}; '
                             f'observed action={outcomes.get(phase)}, counts={counts}')
        if phase == 'seeded-fault' and 'XCTAssertEqual' not in json.dumps(summary.get('testFailures', [])):
            raise ValueError('The seeded failure must be a native equality assertion, not a crash or build failure')
        cases.append(dict(phase=phase, outcome=outcomes[phase], native_counts=dict(zip(
            ('total', 'passed', 'failed', 'skipped'), counts))))
    return dict(status='passed', evidence_kind='controlled-native-baseline', live_planner_executed=False,
                fault_kind='seeded-shared-preference-key', upstream_defect_claim=False,
                provenance=provenance, mutation=mutation, cases=cases)


if __name__ == '__main__':
    root = Path('proof')
    result = verify(root, {'original': os.environ['ORIGINAL_OUTCOME'],
                           'seeded-fault': os.environ['FAULT_OUTCOME'],
                           'restored': os.environ['RESTORED_OUTCOME']})
    (root / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    provenance = result['provenance']
    lines = ['# Controlled keyboard-preference regression proof', '',
             'The original and restored app passed the same native UI test. A deliberately seeded shared-key fault '
             'failed a native equality assertion. The test and its assertions were unchanged.', '',
             '**This is a seeded-fault baseline demonstration. It is not an upstream bug discovery or a live '
             'model-generated release test.**', '',
             f'- Source snapshot: `{provenance["source_sha"]}`',
             f'- Harness: `{provenance["harness_sha"]}`',
             f'- UI Check: `{provenance["action_sha"]}`',
             f'- Workflow: {provenance["run_url"]}', '',
             '| App variant | Native pass | Native fail | Native skip |', '| --- | --- | --- |']
    for case in result['cases']:
        counts = case['native_counts']
        lines.append(f'| {case["phase"]} | {counts["passed"]} | {counts["failed"]} | {counts["skipped"]} |')
    lines += ['', 'The fault makes App Launch and New Tab incorrectly share one preference key. '
              'The UI test checks independent values, navigation and relaunch persistence. '
              'The archive retains the one-line patch, original/fault/restored source hashes, '
              'native `.xcresult` bundles, logs, media and source identities.']
    (root / 'report.md').write_text('\n'.join(lines) + '\n')
