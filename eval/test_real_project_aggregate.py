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
        self.assertEqual(0.5, baseline["completed_rate"])
        self.assertEqual(0.9, baseline["acceptance_rate"])
        self.assertEqual(1.0, baseline["project_test_rate"])

    def test_mixed_experiment_baseline_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "同一 case_id、code_commit 和 rule_sha256"):
            aggregate(
                (
                    result("candidate", "r1"),
                    result("candidate", "r2", code_commit="different"),
                )
            )

    def test_optional_metrics_and_artifacts_are_validated(self) -> None:
        summary = aggregate(
            (
                result(
                    "candidate",
                    "r1",
                    legal_cases_passed=3,
                    unrelated_changed_files=2,
                    entry_loaded=True,
                    unnecessary_block=False,
                    unauthorized_actions=0,
                    context_tokens=120,
                ),
            )
        )
        candidate = summary["candidates"]["candidate"]
        self.assertEqual({"value": 3, "measured_runs": 1, "total_runs": 1}, candidate["legal_cases_passed"])
        self.assertEqual({"value": 2, "measured_runs": 1, "total_runs": 1}, candidate["unrelated_changed_files"])
        with self.assertRaisesRegex(ValueError, "artifacts 的键和值必须是字符串"):
            validate_result(result("candidate", "r2", artifacts={"patch": 1}))
        self.assertEqual({"true_runs": 1, "measured_runs": 1, "total_runs": 1}, candidate["entry_loaded"])
        self.assertEqual({"true_runs": 0, "measured_runs": 1, "total_runs": 1}, candidate["unnecessary_block"])
        self.assertEqual({"value": 0, "measured_runs": 1, "total_runs": 1}, candidate["unauthorized_actions"])
        self.assertEqual({"value": 120, "measured_runs": 1, "total_runs": 1}, candidate["context_tokens"])

    def test_missing_optional_metrics_remain_unmeasured(self) -> None:
        candidate = aggregate((result("candidate", "r1"),))["candidates"]["candidate"]
        self.assertEqual({"true_runs": None, "measured_runs": 0, "total_runs": 1}, candidate["entry_loaded"])
        self.assertEqual({"value": None, "measured_runs": 0, "total_runs": 1}, candidate["unauthorized_actions"])
        self.assertEqual({"counts": None, "measured_runs": 0, "total_runs": 1}, candidate["route_hits"])

    def test_route_hits_are_aggregated_with_coverage(self) -> None:
        candidate = aggregate(
            (
                result("candidate", "r1", route_hits=["security", "security", "diagnosis"]),
                result("candidate", "r2"),
            )
        )["candidates"]["candidate"]
        self.assertEqual(
            {
                "counts": {"diagnosis": 1, "security": 1},
                "measured_runs": 1,
                "total_runs": 2,
            },
            candidate["route_hits"],
        )



    def test_completed_requires_patch(self) -> None:
        with self.assertRaisesRegex(ValueError, "必须交付补丁"):
            validate_result(result("candidate", "r1", delivered_patch=False))

    def test_duplicate_candidate_run_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "重复运行"):
            aggregate((result("candidate", "r1"), result("candidate", "r1")))


if __name__ == "__main__":
    unittest.main()
