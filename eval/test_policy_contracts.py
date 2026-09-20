"""P0 规则语义和入口契约的回归测试。结构检查只证明文本存在，不证明真实行为。"""

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

    def test_all_editions_expose_standalone_safety_baseline(self) -> None:
        for relative_path in ("mini/agent.md", "lite/agent.md", "rules/agent.md", "self/core.md"):
            with self.subTest(relative_path=relative_path):
                policy = read_rule(relative_path)
                for text in (
                    "可信输入",
                    "密钥",
                    "外部输入",
                    "破坏性测试",
                    "不提交",
                    "不推送",
                    "不改写版本历史",
                ):
                    self.assertIn(text, policy)

    def test_all_editions_expose_final_result_contract(self) -> None:
        for relative_path in ("mini/agent.md", "lite/agent.md", "rules/agent.md", "self/core.md"):
            with self.subTest(relative_path=relative_path):
                policy = read_rule(relative_path)
                self.assertIn("## 最终结果契约", policy)
                for field in ("status: completed | blocked | failed", "summary:", "changed_files:", "validation:", "remaining_risks:", "next_step:"):
                    self.assertIn(field, policy)

    def test_all_editions_define_inline_constraint_format(self) -> None:
        for relative_path in ("mini/agent.md", "lite/agent.md", "rules/agent.md", "self/core.md"):
            with self.subTest(relative_path=relative_path):
                self.assertIn("constraint:", read_rule(relative_path))

    def test_security_routes_are_available_for_mini_and_lite(self) -> None:
        for edition in ("mini", "lite"):
            with self.subTest(edition=edition):
                self.assertTrue((ROOT / edition / "methods" / "security.md").is_file())
                self.assertIn("methods/security.md", read_rule(f"{edition}/triggers.md"))

    def test_audit_record_heading_is_stable(self) -> None:
        log = read_rule("documents/decision-log.md")
        destructive = read_rule("rules/destructive-analysis.md")
        self.assertIn("## 变更审计记录", log)
        self.assertIn("`/documents/decision-log.md`「变更审计记录」", destructive)

    def test_reference_checker_ignores_generated_and_vendor_trees(self) -> None:
        from eval import check_rule_references

        paths = check_rule_references.MARKDOWN_FILES
        self.assertTrue(paths)
        self.assertTrue(all(not (".kilo" in path.parts or "node_modules" in path.parts) for path in paths))
        self.assertIn(ROOT / "rules" / "agent.md", paths)

    def test_document_templates_are_machine_marked(self) -> None:
        for path in (ROOT / "documents").glob("*.md"):
            with self.subTest(path=path.name):
                content = path.read_text(encoding="utf-8")
                self.assertTrue(content.startswith("---\n") or content.startswith("---\r\n"))
                self.assertIn("document_status: template", content[:120])
                self.assertIn("project_facts: none", content[:120])

    def test_all_editions_expose_status_and_continuation_gate(self) -> None:
        for relative_path in ("mini/agent.md", "lite/agent.md", "rules/agent.md", "self/core.md"):
            with self.subTest(relative_path=relative_path):
                policy = read_rule(relative_path)
                self.assertIn("状态与继续门禁", policy)
                for phrase in ("有效进展", "写入前", "继续前", "完成前"):
                    self.assertIn(phrase, policy)

    def test_status_gate_semantics_are_aligned(self) -> None:
        required_fragments = (
            "默认依据适用证据推进下一可验证动作",
            "每次调查、验证或执行的可观察逻辑动作结束后检查",
            "同一路径无有效进展时，下次尝试须说明改变了什么",
            "写入前",
            "继续前",
            "拟执行动作超出授权范围时暂停越界动作",
            "平台或用户提供的上下文、步骤或时间预算接近上限时",
            "完成前",
        )
        for relative_path in ("mini/agent.md", "lite/agent.md", "rules/agent.md", "self/core.md"):
            with self.subTest(relative_path=relative_path):
                policy = read_rule(relative_path)
                for fragment in required_fragments:
                    self.assertIn(fragment, policy)

    def test_decision_evidence_contracts(self) -> None:
        for relative_path in (
            "rules/business-analysis.md",
            "mini/methods/decision-recall.md",
            "lite/methods/decision-recall.md",
        ):
            with self.subTest(relative_path=relative_path):
                policy = read_rule(relative_path)
                for phrase in ("新建决策条件", "依据生命周期", "未来复用价值", "当前依赖", "留存义务"):
                    self.assertIn(phrase, policy)
                self.assertNotIn("仅在条件满足时才重新评估", policy)

    def test_self_supports_local_selection_evidence(self) -> None:
        self.assertIn("context.md", read_rule("self/core.md"))
        context = read_rule("self/context.md")
        self.assertIn("## 选择依据", context)
        self.assertIn("不要求建立独立决策档案", context)
        self.assertIn("未提交记录", context)

    def test_modeling_methods_remain_reachable_after_extraction(self) -> None:
        for entry, method in (
            ("mini/agent.md", "mini/methods/project-context.md"),
            ("lite/agent.md", "lite/methods/project-context.md"),
            ("self/core.md", "self/context.md"),
            ("rules/agent.md", "rules/coding-principles.md"),
        ):
            with self.subTest(entry=entry):
                self.assertIn(Path(method).name, read_rule(entry))
                self.assertIn("最小充分模型", read_rule(method))

    def test_case_n_documents_state_gate_evaluation_protocol(self) -> None:
        case_n = read_rule("eval/case-n-operational-criteria.md")
        eval_readme = read_rule("eval/README.md")
        self.assertIn("### 状态与继续门禁（四版通用）", case_n)
        for phrase in ("文字假进展变体", "统计采样变体", "验证未完成的交付变体", "预算与恢复"):
            self.assertIn(phrase, case_n)
        self.assertIn("### 状态门禁的 A/B 评测", eval_readme)


if __name__ == "__main__":
    unittest.main()
