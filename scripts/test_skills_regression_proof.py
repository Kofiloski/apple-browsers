import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('proof', Path(__file__).with_name('skills-verify-regression-proof.py'))
proof = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proof)


class ProofTests(unittest.TestCase):
    def fixture(self, root):
        (root / 'provenance.json').write_text(json.dumps(dict(source_sha='a' * 40,
            harness_sha='b' * 40, action_sha='c' * 40)))
        (root / 'mutation.json').write_text(json.dumps(dict(original_sha256='a' * 64,
            fault_sha256='b' * 64, restored_sha256='a' * 64, fault_patch_sha256='c' * 64)))
        for phase, passed, failed in [('original', 1, 0), ('seeded-fault', 0, 1), ('restored', 1, 0)]:
            (root / phase).mkdir()
            (root / phase / 'test-results.json').write_text(json.dumps(dict(totalTestCount=1,
                passedTests=passed, failedTests=failed, skippedTests=0,
                testFailures=[dict(failureText='XCTAssertEqual failed: 1 versus 0')] if failed else [])))
        return {'original': 'success', 'seeded-fault': 'failure', 'restored': 'success'}

    def test_accepts_native_failure_between_two_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outcomes = self.fixture(root)
            result = proof.verify(root, outcomes)
            self.assertEqual(result['status'], 'passed')
            self.assertFalse(result['live_planner_executed'])
            self.assertFalse(result['upstream_defect_claim'])

    def test_rejects_skip_crash_and_an_undetected_fault(self):
        for summary in [dict(totalTestCount=1, passedTests=0, failedTests=0, skippedTests=1),
                        dict(totalTestCount=1, passedTests=0, failedTests=1, skippedTests=0,
                             testFailures=[dict(failureText='The app crashed')]),
                        dict(totalTestCount=1, passedTests=1, failedTests=0, skippedTests=0)]:
            with self.subTest(summary=summary), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                outcomes = self.fixture(root)
                (root / 'seeded-fault/test-results.json').write_text(json.dumps(summary))
                with self.assertRaises(ValueError):
                    proof.verify(root, outcomes)

    def test_rejects_failed_restore_and_changed_restored_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outcomes = self.fixture(root)
            with self.assertRaises(ValueError):
                proof.verify(root, dict(outcomes, restored='failure'))
            mutation = json.loads((root / 'mutation.json').read_text())
            mutation['restored_sha256'] = 'd' * 64
            (root / 'mutation.json').write_text(json.dumps(mutation))
            with self.assertRaises(ValueError):
                proof.verify(root, outcomes)


if __name__ == '__main__':
    unittest.main()
