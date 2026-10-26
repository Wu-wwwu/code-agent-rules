"""模糊程度词必须落到可操作判定条件的回归测试。"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read_rule(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class OperationalCriteriaTests(unittest.TestCase):
    def test_all_editions_define_evidence_reuse_conditions(self) -> None:
        for relative_path in ("rules/agent.md", "mini/agent.md", "lite/agent.md", "self/core.md"):
            with self.subTest(relative_path=relative_path):
                policy = read_rule(relative_path)
                for text in ("来源", "目标", "范围", "分支/环境", "截断", "冲突"):
                    self.assertIn(text, policy)

    def test_all_editions_define_stable_boundary_and_verification_seam(self) -> None:
        for relative_path in (
            "rules/agent.md",
            "mini/methods/project-context.md",
            "lite/agent.md",
            "self/context.md",
        ):
            with self.subTest(relative_path=relative_path):
                policy = read_rule(relative_path)
                self.assertIn("稳定边界", policy)
                self.assertIn("验证接缝", policy)
                self.assertRegex(policy, r"(响应|公开响应)")
                self.assertIn("持久化状态", policy)

    def test_high_rollback_cost_has_observable_conditions(self) -> None:
        for relative_path in ("rules/agent.md", "mini/agent.md", "lite/agent.md", "self/core.md"):
            with self.subTest(relative_path=relative_path):
                policy = read_rule(relative_path)
                for pattern in (
                    r"恢复(?:/|或)重算",
                    r"协调(?:多个)?消费者",
                    r"停机/切流",
                    r"跨环境同步",
                    r"撤销外部副作用",
                    r"(?:没有经过验证的恢复路径|尚无已验证路径)",
                ):
                    self.assertRegex(policy, pattern)

    def test_delegation_uses_independence_and_exclusion_conditions(self) -> None:
        for relative_path in (
            "rules/agent-collaboration.md",
            "mini/methods/multi-agent.md",
            "lite/methods/multi-agent.md",
            "self/collaboration.md",
        ):
            with self.subTest(relative_path=relative_path):
                policy = read_rule(relative_path)
                self.assertIn("独立完成标准", policy)
                self.assertIn("尚未产生的前序结果", policy)
                self.assertIn("一次工具调用", policy)
                self.assertIn("共享状态", policy)

    def test_diagnosis_does_not_trade_symptom_fidelity_for_speed(self) -> None:
        for relative_path in (
            "rules/diagnosing-bugs.md",
            "mini/methods/bug-diagnosis.md",
            "lite/methods/bug-diagnosis.md",
        ):
            with self.subTest(relative_path=relative_path):
                policy = read_rule(relative_path)
                self.assertIn("原始症状", policy)
                self.assertIn("记录单次", policy)
                self.assertIn("输入", policy)
                self.assertIn("时序", policy)
                self.assertRegex(policy, r"再删除任一")

    def test_strong_migration_plan_has_minimum_fields(self) -> None:
        policy = read_rule("rules/destructive-analysis.md")
        for text in (
            "前后不变量",
            "批次边界",
            "兼容策略",
            "校验和",
            "错误阈值",
            "停止条件",
            "监控观察点",
            "代码/数据/流量恢复步骤",
            "不可逆部分",
        ):
            self.assertIn(text, policy)

    def test_all_editions_preserve_utf8_bom_bytes(self) -> None:
        for relative_path in ("rules/coding-principles.md", "mini/agent.md", "lite/agent.md", "self/core.md"):
            with self.subTest(relative_path=relative_path):
                policy = read_rule(relative_path)
                self.assertIn("保留文件编码", policy)
                self.assertIn("原有 BOM 状态", policy)
                self.assertIn("EF BB BF", policy)
                self.assertIn("不得新增", policy)
                self.assertIn("视为文件内容", policy)


if __name__ == "__main__":
    unittest.main()