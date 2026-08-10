"""终态代码收束与逻辑闭合语义的回归测试。"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read_rule(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class CompletionPolicyTests(unittest.TestCase):
    def test_all_editions_expose_completion_gates(self) -> None:
        for relative_path in (
            "mini/agent.md",
            "lite/agent.md",
            "rules/agent.md",
            "self/core.md",
        ):
            with self.subTest(relative_path=relative_path):
                policy = read_rule(relative_path)
                self.assertIn("代码收束", policy)
                self.assertIn("逻辑闭合", policy)
                self.assertIn("无消费者", policy)
                self.assertRegex(policy, r"范围外(?:旧债|技术债)")
                self.assertIn("未接线实现", policy)

    def test_completion_gates_preserve_legitimate_old_paths_and_read_only_scope(self) -> None:
        for relative_path in ("mini/agent.md", "lite/agent.md", "rules/agent.md", "self/core.md"):
            with self.subTest(relative_path=relative_path):
                policy = read_rule(relative_path)
                self.assertIn("移除条件", policy)
                self.assertRegex(policy, r"(?:无|没有)实现产物")

    def test_strong_policy_requires_end_to_end_completion_evidence(self) -> None:
        policy = read_rule("rules/agent.md")
        for required_text in (
            "每项成功标准都能追溯到可达的实现路径和匹配的验证证据",
            "失败/超时/取消/部分成功处理",
            "新增入口必须接到实现",
            "新增实现必须有当前消费者",
            "变更结果必须被调用方或后续节点正确处理",
        ):
            self.assertIn(required_text, policy)


if __name__ == "__main__":
    unittest.main()