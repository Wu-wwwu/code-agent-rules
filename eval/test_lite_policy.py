"""Lite edition semantic regression tests."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_rule(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class LitePolicyTests(unittest.TestCase):
    def test_task_environment_is_evidence_based_slice(self) -> None:
        policy = read_rule("lite/methods/project-context.md")
        for text in ("环境切片", "不是完整项目模型", "当前实现事实", "待验证推断", "未知与冲突", "证据位置"):
            self.assertIn(text, policy)

    def test_subagent_context_and_acceptance_protocol(self) -> None:
        policy = read_rule("lite/methods/multi-agent.md")
        for text in ("不复制整个会话", "非目标/禁止操作", "约束与依赖", "共享资源所有者", "accepted", "needs-verification", "needs-rework", "blocked", "只有 `accepted`", "恢复单 Agent"):
            self.assertIn(text, policy)

    def test_entry_and_route_expose_fact_states_and_handoff(self) -> None:
        agent = read_rule("lite/agent.md")
        triggers = read_rule("lite/triggers.md")
        for text in ("已验证事实", "待验证推断", "未知与冲突"):
            self.assertIn(text, agent)
        self.assertIn("需建立/移交任务环境", triggers)


if __name__ == "__main__":
    unittest.main()