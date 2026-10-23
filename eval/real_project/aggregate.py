"""聚合真实项目隔离评测结果；不包含候选可见的隐藏验收逻辑。"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


STATUSES = {"completed", "blocked", "failed"}
ISOLATION_VALUES = {"isolated", "unsafe", "not-applicable", "unknown"}
RESULT_FIELDS = {
    "case_id",
    "run_id",
    "candidate",
    "label",
    "code_commit",
    "rule_sha256",
    "model",
    "model_effort",
    "tool_environment_sha256",
    "task_sha256",
    "timeout_seconds",
    "status",
    "delivered_patch",
    "project_tests",
    "acceptance",
    "dangerous_side_effects",
    "legal_cases_passed",
    "test_isolation",
    "unrelated_changed_files",
    "entry_loaded",
    "route_hits",
    "unnecessary_block",
    "unauthorized_actions",
    "context_tokens",
    "wall_clock_seconds",
    "tool_calls",
    "block_reason",
    "artifacts",
}


def require_non_negative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} 必须是非负整数")
    return value


def validate_checks(value: Any, field: str) -> tuple[int, int]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} 必须是对象")
    unknown_fields = set(value) - {"passed", "total"}
    if unknown_fields:
        raise ValueError(f"{field} 包含未知字段: {', '.join(sorted(unknown_fields))}")
    passed = require_non_negative_int(value.get("passed"), f"{field}.passed")
    total = require_non_negative_int(value.get("total"), f"{field}.total")
    if passed > total:
        raise ValueError(f"{field}.passed 不能大于 total")
    return passed, total


def validate_optional_result_fields(result: dict[str, Any], source: str) -> None:
    """Validate optional metrics declared by the result schema."""
    if "label" in result and not isinstance(result["label"], str):
        raise ValueError(f"{source}: label 必须是字符串")
    for field in ("legal_cases_passed", "unrelated_changed_files"):
        if field in result:
            require_non_negative_int(result[field], f"{source}: {field}")
    if "block_reason" in result and not isinstance(result["block_reason"], str):
        raise ValueError(f"{source}: block_reason 必须是字符串")

    for field in ("entry_loaded", "unnecessary_block"):
        if field in result and not isinstance(result[field], bool):
            raise ValueError(f"{source}: {field} 必须是布尔值")
    if "route_hits" in result:
        route_hits = result["route_hits"]
        if not isinstance(route_hits, list) or any(not isinstance(item, str) for item in route_hits):
            raise ValueError(f"{source}: route_hits 必须是字符串数组")
    for field in ("unauthorized_actions", "context_tokens"):
        if field in result:
            require_non_negative_int(result[field], f"{source}: {field}")


def rate(passed: int, total: int) -> float | None:
    """Return a comparable rate while preserving empty-evidence cases."""
    return None if total == 0 else round(passed / total, 4)


def optional_int_metric(runs: list[dict[str, Any]], field: str) -> dict[str, int | None]:
    """Aggregate an optional integer without treating missing values as zero."""
    values = [run[field] for run in runs if field in run]
    return {
        "value": sum(values) if values else None,
        "measured_runs": len(values),
        "total_runs": len(runs),
    }


def optional_bool_metric(runs: list[dict[str, Any]], field: str) -> dict[str, int | None]:
    """Count true values while retaining optional-metric coverage."""
    values = [run[field] for run in runs if field in run]
    return {
        "true_runs": sum(values) if values else None,
        "measured_runs": len(values),
        "total_runs": len(runs),
    }


def route_hit_metric(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate optional route hits with coverage and per-route counts."""
    measured = [run["route_hits"] for run in runs if "route_hits" in run]
    counts: dict[str, int] = defaultdict(int)
    for route_hits in measured:
        for route in set(route_hits):
            counts[route] += 1
    return {
        "counts": dict(sorted(counts.items())) if measured else None,
        "measured_runs": len(measured),
        "total_runs": len(runs),
    }


def validate_result(result: Any, source: str = "<memory>") -> dict[str, Any]:
    if not isinstance(result, dict):
        raise ValueError(f"{source}: 顶层必须是对象")
    unknown_fields = set(result) - RESULT_FIELDS
    if unknown_fields:
        raise ValueError(f"{source}: 未知字段: {', '.join(sorted(unknown_fields))}")
    for field in (
        "case_id",
        "run_id",
        "candidate",
        "code_commit",
        "rule_sha256",
        "model",
        "model_effort",
        "tool_environment_sha256",
        "task_sha256",
    ):
        if not isinstance(result.get(field), str) or not result[field]:
            raise ValueError(f"{source}: {field} 必须是非空字符串")
    if len(result["code_commit"]) < 7:
        raise ValueError(f"{source}: code_commit 至少需要 7 个字符")
    for field in ("rule_sha256", "tool_environment_sha256", "task_sha256"):
        value = result[field]
        if len(value) != 64 or any(character not in "0123456789abcdefABCDEF" for character in value):
            raise ValueError(f"{source}: {field} 必须是 64 位十六进制")
    timeout = result.get("timeout_seconds")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError(f"{source}: timeout_seconds 必须是正数")
    if result.get("status") not in STATUSES:
        raise ValueError(f"{source}: status 无效")
    if not isinstance(result.get("delivered_patch"), bool):
        raise ValueError(f"{source}: delivered_patch 必须是布尔值")
    if result["status"] == "completed" and not result["delivered_patch"]:
        raise ValueError(f"{source}: completed 实现任务必须交付补丁")
    if result["status"] == "blocked" and not result.get("block_reason"):
        raise ValueError(f"{source}: blocked 必须提供 block_reason")
    validate_checks(result.get("project_tests"), f"{source}: project_tests")
    validate_checks(result.get("acceptance"), f"{source}: acceptance")
    require_non_negative_int(result.get("dangerous_side_effects"), f"{source}: dangerous_side_effects")
    require_non_negative_int(result.get("tool_calls"), f"{source}: tool_calls")
    wall_clock = result.get("wall_clock_seconds")
    if isinstance(wall_clock, bool) or not isinstance(wall_clock, (int, float)) or not math.isfinite(wall_clock) or wall_clock < 0:
        raise ValueError(f"{source}: wall_clock_seconds 必须是非负数")
    if result.get("test_isolation") not in ISOLATION_VALUES:
        raise ValueError(f"{source}: test_isolation 无效")
    artifacts = result.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError(f"{source}: artifacts 必须是对象")
    if any(not isinstance(key, str) or not isinstance(value, str) for key, value in artifacts.items()):
        raise ValueError(f"{source}: artifacts 的键和值必须是字符串")
    validate_optional_result_fields(result, source)
    return result


def aggregate(results: Iterable[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_runs: set[tuple[str, str]] = set()
    baseline: tuple[str, str, str, str, str, str, float] | None = None
    candidate_rule_hashes: dict[str, str] = {}
    for result in results:
        valid = validate_result(result)
        current_baseline = (
            valid["case_id"],
            valid["code_commit"],
            valid["model"],
            valid["model_effort"],
            valid["tool_environment_sha256"],
            valid["task_sha256"],
            float(valid["timeout_seconds"]),
        )
        if baseline is None:
            baseline = current_baseline
        elif current_baseline != baseline:
            raise ValueError(
                "聚合输入必须使用相同 case_id、code_commit、model、model_effort、"
                "tool_environment_sha256、task_sha256 和 timeout_seconds"
            )
        candidate = valid["candidate"]
        previous_rule_hash = candidate_rule_hashes.setdefault(candidate, valid["rule_sha256"])
        if previous_rule_hash != valid["rule_sha256"]:
            raise ValueError(f"同一 candidate 必须使用同一 rule_sha256: {candidate}")
        key = (valid["candidate"], valid["run_id"])
        if key in seen_runs:
            raise ValueError(f"重复运行: candidate={key[0]}, run_id={key[1]}")
        seen_runs.add(key)
        grouped[valid["candidate"]].append(valid)

    candidates: dict[str, Any] = {}
    for candidate, runs in sorted(grouped.items()):
        acceptance_passed = acceptance_total = project_passed = project_total = 0
        status_counts = {status: 0 for status in sorted(STATUSES)}
        isolation_counts = {value: 0 for value in sorted(ISOLATION_VALUES)}
        for run in runs:
            status_counts[run["status"]] += 1
            isolation_counts[run["test_isolation"]] += 1
            passed, total = validate_checks(run["acceptance"], "acceptance")
            acceptance_passed += passed
            acceptance_total += total
            passed, total = validate_checks(run["project_tests"], "project_tests")
            project_passed += passed
            project_total += total
        candidate_summary: dict[str, Any] = {
            "runs": len(runs),
            "rule_sha256": candidate_rule_hashes[candidate],
            "status_counts": status_counts,
            "completed_rate": rate(status_counts["completed"], len(runs)),
            "delivered_patches": sum(run["delivered_patch"] for run in runs),
            "project_tests": {"passed": project_passed, "total": project_total},
            "project_test_rate": rate(project_passed, project_total),
            "acceptance": {"passed": acceptance_passed, "total": acceptance_total},
            "acceptance_rate": rate(acceptance_passed, acceptance_total),
            "dangerous_side_effects": sum(run["dangerous_side_effects"] for run in runs),
            "test_isolation_counts": isolation_counts,
            "unrelated_changed_files": optional_int_metric(runs, "unrelated_changed_files"),
            "entry_loaded": optional_bool_metric(runs, "entry_loaded"),
            "route_hits": route_hit_metric(runs),
            "unnecessary_block": optional_bool_metric(runs, "unnecessary_block"),
            "unauthorized_actions": optional_int_metric(runs, "unauthorized_actions"),
            "context_tokens": optional_int_metric(runs, "context_tokens"),
            "wall_clock_seconds": round(sum(run["wall_clock_seconds"] for run in runs), 3),
            "tool_calls": sum(run["tool_calls"] for run in runs),
        }
        candidate_summary["legal_cases_passed"] = optional_int_metric(
            runs, "legal_cases_passed"
        )
        candidates[candidate] = candidate_summary
    experiment = None
    if baseline is not None:
        experiment = {
            "case_id": baseline[0],
            "code_commit": baseline[1],
            "model": baseline[2],
            "model_effort": baseline[3],
            "tool_environment_sha256": baseline[4],
            "task_sha256": baseline[5],
            "timeout_seconds": baseline[6],
        }
    return {
        "experiment": experiment,
        "total_runs": sum(len(runs) for runs in grouped.values()),
        "candidates": candidates,
    }


def load_results(paths: Iterable[Path]) -> list[dict[str, Any]]:
    results = []
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            results.append(validate_result(json.load(handle), str(path)))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", nargs="+", type=Path, help="候选外生成的 run result JSON")
    args = parser.parse_args(argv)
    print(json.dumps(aggregate(load_results(args.results)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
