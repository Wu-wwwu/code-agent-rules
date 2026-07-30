"""真实项目评测结果聚合器测试。"""

from __future__ import annotations

import unittest

from eval.real_project.aggregate import aggregate, validate_result


def result(candidate: str, run_id: str, **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "case_id": "installer-self-overwrite",
        "run_id": run_id,
        "candidate": candidate,
        "code_commit": "81d2002",
        "rule_sha256": "a" * 64,
        "status": "completed",
        "delivered_patch": True,
        "project_tests": {"passed": 11, "total": 11},
        "acceptance": {"passed": 80, "total": 80},
        "dangerous_side_effects": 0,
        "test_isolation": "isolated",
        "wall_clock_seconds": 2.5,
        "tool_calls": 4,
        "artifacts": {"patch": "candidate.patch"},
    }
    value.update(overrides)
    return value


class RealProjectAggregateTests(unittest.TestCase):
    def test_aggregate_groups_candidates_and_sums_evidence(self) -> None:
        summary = aggregate(
            (
                result("baseline", "r1", status="blocked", delivered_patch=False, block_reason="no writer", acceptance={"passed": 64, "total": 80}, dangerous_side_effects=4, test_isolation="not-applicable"),
                result("baseline", "r2"),
                result("redesigned", "r1"),
            )
        )
        self.assertEqual(3, summary["total_runs"])
        baseline = summary["candidates"]["baseline"]
        self.assertEqual(1, baseline["delivered_patches"])
        self.assertEqual({"passed": 144, "total": 160}, baseline["acceptance"])
        self.assertEqual(4, baseline["dangerous_side_effects"])

    def test_completed_requires_patch(self) -> None:
        with self.assertRaisesRegex(ValueError, "必须交付补丁"):
            validate_result(result("candidate", "r1", delivered_patch=False))

    def test_duplicate_candidate_run_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "重复运行"):
            aggregate((result("candidate", "r1"), result("candidate", "r1")))


if __name__ == "__main__":
    unittest.main()