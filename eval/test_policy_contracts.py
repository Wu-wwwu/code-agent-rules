"""P0 规则语义和入口契约的回归测试。"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read_rule(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class PolicyContractTests(unittest.TestCase):
    def test_all_editions_define_blocked_fallback(self) -> None:
        for relative_path in ("mini/agent.md", "lite/agent.md", "rules/agent.md", "self/core.md"):
            with self.subTest(relative_path=relative_path):
                policy = read_rule(relative_path)
                self.assertIn("status: blocked", policy)
                self.assertIn("缺失确认", policy)
                self.assertIn("只读证据", policy)
                self.assertIn("未执行", policy)
                self.assertIn("解除条件", policy)
                self.assertIn("沉默", policy)

    def test_record_types_are_distinct(self) -> None:
        destructive = read_rule("rules/destructive-analysis.md")
        business = read_rule("rules/business-analysis.md")
        self.assertIn("变更审计记录", destructive)
        self.assertIn("决策记录", destructive)
        self.assertIn("不等于技术决策", destructive)
        self.assertIn("不因审计记录自动创建决策", business)

    def test_lite_user_goal_does_not_override_safety_gates(self) -> None:
        policy = read_rule("lite/agent.md")
        self.assertIn("不得覆盖安全、授权、隔离、不可逆变更和强制验证门禁", policy)


if __name__ == "__main__":
    unittest.main()
