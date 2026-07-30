"""聚合真实项目隔离评测结果；不包含候选可见的隐藏验收逻辑。"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


STATUSES = {"completed", "blocked", "failed"}
ISOLATION_VALUES = {"isolated", "unsafe", "not-applicable", "unknown"}


def require_non_negative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} 必须是非负整数")
    return value


def validate_checks(value: Any, field: str) -> tuple[int, int]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} 必须是对象")
    passed = require_non_negative_int(value.get("passed"), f"{field}.passed")
    total = require_non_negative_int(value.get("total"), f"{field}.total")
    if passed > total:
        raise ValueError(f"{field}.passed 不能大于 total")
    return passed, total


def validate_result(result: Any, source: str = "<memory>") -> dict[str, Any]:
    if not isinstance(result, dict):
        raise ValueError(f"{source}: 顶层必须是对象")
    for field in ("case_id", "run_id", "candidate", "code_commit", "rule_sha256"):
        if not isinstance(result.get(field), str) or not result[field]:
            raise ValueError(f"{source}: {field} 必须是非空字符串")
    if len(result["rule_sha256"]) != 64 or any(character not in "0123456789abcdefABCDEF" for character in result["rule_sha256"]):
        raise ValueError(f"{source}: rule_sha256 必须是 64 位十六进制")
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
    if isinstance(wall_clock, bool) or not isinstance(wall_clock, (int, float)) or wall_clock < 0:
        raise ValueError(f"{source}: wall_clock_seconds 必须是非负数")
    if result.get("test_isolation") not in ISOLATION_VALUES:
        raise ValueError(f"{source}: test_isolation 无效")
    if not isinstance(result.get("artifacts"), dict):
        raise ValueError(f"{source}: artifacts 必须是对象")
    return result


def aggregate(results: Iterable[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_runs: set[tuple[str, str]] = set()
    for result in results:
        valid = validate_result(result)
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
        candidates[candidate] = {
            "runs": len(runs),
            "status_counts": status_counts,
            "delivered_patches": sum(run["delivered_patch"] for run in runs),
            "project_tests": {"passed": project_passed, "total": project_total},
            "acceptance": {"passed": acceptance_passed, "total": acceptance_total},
            "dangerous_side_effects": sum(run["dangerous_side_effects"] for run in runs),
            "test_isolation_counts": isolation_counts,
            "wall_clock_seconds": round(sum(run["wall_clock_seconds"] for run in runs), 3),
            "tool_calls": sum(run["tool_calls"] for run in runs),
        }
    return {"total_runs": sum(len(runs) for runs in grouped.values()), "candidates": candidates}


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