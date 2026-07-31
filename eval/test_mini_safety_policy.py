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
            "不兼容改变公开 API/共享契约",
            "取得覆盖这些内容的明确确认",
            "可能为高风险时先暂停补证据",
        ):
            self.assertIn(required_text, policy)

    def test_destructive_policy_defines_authorization_outcomes(self):
        policy = read_rule("mini/methods/destructive-analysis.md")

        for outcome in (
            "**确认**",
            "**修改要求**",
            "**拒绝**",
            "**未回复/含糊**",
            "原授权失效并重新分析",
        ):
            self.assertIn(outcome, policy)

    def test_destructive_policy_reuse_compares_change_elements(self):
        policy = read_rule("mini/methods/destructive-analysis.md")

        self.assertIn("任一变化，原授权失效并重新分析", policy)
        for element in ("目标环境", "操作", "契约与消费者", "授权条件"):
            self.assertIn(element, policy)

    def test_agent_and_routes_connect_risk_to_mandatory_methods(self):
        agent = read_rule("mini/agent.md")
        triggers = read_rule("mini/triggers.md")

        self.assertIn("新任务或范围变化时读取 `triggers.md`", agent)
        self.assertIn("只加载当前动作需要的最少方法", agent)
        self.assertIn("任何方法都不能替代另一方法的门禁", triggers)
        self.assertIn("Bug 优先走诊断", triggers)
        self.assertIn("权限执行风险走破坏性分析", triggers)
        self.assertIn("权限目标语义不明时再叠加业务规则", triggers)

    def test_dependency_confirmation_uses_shared_state_transitions(self):
        policy = read_rule("mini/methods/dependency-upgrade.md")

        self.assertIn("修改版本或代码前", policy)
        self.assertIn("形成影响清单", policy)
        self.assertIn("再执行修改", policy)
        self.assertIn("逐处或分类请求确认", policy)
        self.assertIn("分级、方案与授权门禁", policy)
        self.assertIn("破坏性义务完成后退出", policy)

    def test_business_risk_uses_project_code_data_flow_and_resources(self):
        policy = read_rule("mini/methods/business-rules.md")

        for dimension in ("**代码路径**", "**数据流**", "**业务流程**", "**关键资源**"):
            self.assertIn(dimension, policy)
        self.assertIn("不直接决定风险级别或确认深度", policy)
        self.assertIn("实际后果、影响范围、可检测性与可恢复性", policy)
        self.assertIn("仅当规则缺失/冲突", policy)
        self.assertIn("用户原始请求中的总体方向不是规则证据", policy)
        self.assertIn("多个对照实现冲突时视为无直接依据", policy)
        self.assertIn("用户给出实现方向也不能替代有效规则核对", policy)
        self.assertIn("未回复或回复含糊时保持暂停", policy)

    def test_destructive_grading_uses_project_impact_without_weakening_hard_gates(self):
        policy = read_rule("mini/methods/destructive-analysis.md")

        for dimension in ("**代码、数据、流程、关键资源**",):
            self.assertIn(dimension, policy)
        self.assertIn("项目证据可以升级风险", policy)
        self.assertIn("不得降低已命中的高风险硬门槛", policy)


if __name__ == "__main__":
    unittest.main()