"""Mini 规则关键安全语义的回归测试。"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read_rule(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class MiniSafetyPolicyTests(unittest.TestCase):
    def test_destructive_policy_has_objective_high_risk_gate(self):
        policy = read_rule("mini/methods/destructive-analysis.md")

        for required_text in (
            "按命中的最高级别处理",
            "持久化、共享、用户或生产数据",
            "删除表/列、缩窄字段",
            "权限提升或安全策略放宽",
            "不兼容地删除/改变公开 API 或共享契约",
            "取得明确用户确认后再执行",
            "信息不足且可能命中高风险时先暂停",
        ):
            self.assertIn(required_text, policy)

    def test_destructive_policy_defines_authorization_outcomes(self):
        policy = read_rule("mini/methods/destructive-analysis.md")

        for outcome in (
            "**确认**",
            "**修改要求**",
            "**拒绝**",
            "**未回复或含糊回复**",
            "原授权失效并重新分析",
        ):
            self.assertIn(outcome, policy)

    def test_destructive_policy_reuse_compares_change_elements(self):
        policy = read_rule("mini/methods/destructive-analysis.md")

        self.assertIn("本轮清单相同或为其严格子集", policy)
        for element in ("目标环境", "操作类型", "API、Schema 与下游消费者", "用户授权条件"):
            self.assertIn(element, policy)

    def test_agent_and_routes_connect_risk_to_mandatory_methods(self):
        agent = read_rule("mini/agent.md")
        triggers = read_rule("mini/triggers.md")

        self.assertIn("自动加载 `methods/destructive-analysis.md` 并按其客观条件分级", agent)
        self.assertIn("这些词只触发分析，不直接决定风险级别", agent)
        self.assertIn("不能跳过任何已命中方法规定的", triggers)
        self.assertIn("Bug 任务以 T9 为主", triggers)
        self.assertIn("权限修改命中 T1", triggers)
        self.assertIn("同时命中 T3", triggers)

    def test_dependency_confirmation_uses_shared_state_transitions(self):
        policy = read_rule("mini/methods/dependency-upgrade.md")

        self.assertIn("授权门禁与状态推进", policy)
        self.assertIn("旧确认失效", policy)

    def test_business_risk_uses_project_code_data_flow_and_resources(self):
        policy = read_rule("mini/methods/business-rules.md")

        for dimension in ("**代码路径**", "**数据流**", "**业务流程**", "**关键资源**"):
            self.assertIn(dimension, policy)
        self.assertIn("不直接决定风险级别或确认深度", policy)
        self.assertIn("实际后果、影响范围、可检测性与可恢复性", policy)
        self.assertIn("仅在规则缺失或冲突", policy)
        self.assertIn("未回复或回复含糊时保持暂停", policy)

    def test_destructive_grading_uses_project_impact_without_weakening_hard_gates(self):
        policy = read_rule("mini/methods/destructive-analysis.md")

        for dimension in ("**代码**", "**数据**", "**流程**", "**关键资源**"):
            self.assertIn(dimension, policy)
        self.assertIn("项目画像可以基于证据升级", policy)
        self.assertIn("不得用“项目侧重点不同”", policy)


if __name__ == "__main__":
    unittest.main()