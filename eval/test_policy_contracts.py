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

    def test_current_facts_and_audit_boundaries_are_preserved(self) -> None:
        strong = read_rule("rules/document-init.md")
        self.assertIn("写回内容形成当前基线，不构成永久事实", strong)
        self.assertIn("实现、配置、Schema、测试或运行结果变化时", strong)

        decision = read_rule("rules/business-analysis.md")
        self.assertIn("用户确认只说明目标、约束或授权，不证明实现正确", decision)
        self.assertIn("编号、日期、状态", decision)
        self.assertIn("仅在需要识别生命周期、审计留存或当前依赖时记录", decision)

        audit = read_rule("rules/destructive-analysis.md")
        self.assertIn("可核对的变更事实、适用授权、实际影响、验证结果和残余风险", audit)
        self.assertIn("不等于技术决策", audit)

    def test_minimal_model_distinguishes_data_lifecycles_without_forcing_all_tasks(self) -> None:
        for relative_path in (
            "rules/coding-principles.md",
            "mini/methods/project-context.md",
            "lite/methods/project-context.md",
        ):
            with self.subTest(relative_path=relative_path):
                policy = read_rule(relative_path)
                self.assertIn("内存生命周期", policy)
                self.assertIn("持久化时机", policy)
                self.assertIn("缓存生命周期", policy)
                self.assertIn("消息发送/确认时机", policy)
                self.assertIn("只在某一边界影响当前动作", policy)
                self.assertIn("模型不能改变当前动作或完成判断时，不继续扩展模型", policy)

    def test_case_o_covers_current_facts_lifecycles_and_lightweight_path(self) -> None:
        case = read_rule("eval/case-o-current-facts-and-lifecycles.md")
        eval_index = read_rule("eval/README.md")
        for phrase in (
            "当前证据与旧记录冲突",
            "简单任务轻量路径",
            "多种生命周期边界",
            "决策与审计边界",
            "消息发送与数据库提交时机",
        ):
            self.assertIn(phrase, case)
        self.assertIn("case-o-current-facts-and-lifecycles.md", eval_index)
        self.assertIn("待评测", eval_index)

    def test_module_goal_lifecycle_method_is_routed_and_evaluated(self) -> None:
        entry = read_rule("rules/agent.md")
        method = read_rule("rules/module-development.md")
        case = read_rule("eval/case-p-module-goal-lifecycle.md")
        eval_index = read_rule("eval/README.md")

        self.assertIn("./module-development.md", entry)
        for phrase in ("proposed", "active", "paused", "blocked", "completed", "superseded"):
            self.assertIn(phrase, method)
        self.assertIn("不要求每轮输出完整状态表", method)
        self.assertIn("不替代风险/授权门禁", method)
        self.assertIn("模块未完成，或尚未明确执行清理前，保留仍可能影响本模块", method)
        self.assertIn("同一决策只维护一个权威条目", method)
        self.assertIn("不要求创建模块目录、局部 README", method)
        for phrase in ("局部拼写修复沿轻量路径完成", "superseded", "逐轮决策", "模块局部工作区"):
            self.assertIn(phrase, case)
        self.assertIn("case-p-module-goal-lifecycle.md", eval_index)
        self.assertIn("待评测", eval_index)

    def test_minimal_implementation_is_compact_and_avoids_arbitrary_thresholds(self) -> None:
        policy = read_rule("rules/minimal-implementation.md")
        coding = read_rule("rules/coding-principles.md")
        for phrase in (
            "目标必要性",
            "现有实现",
            "平台能力",
            "现有依赖",
            "最小正确实现",
            "维护/安全/许可/运行影响",
            "无当前消费者且无留存义务时删除",
        ):
            self.assertIn(phrase, policy)
        self.assertNotRegex(policy, r"50\s*行|stars\s*>?\s*1000|GitHub stars")
        self.assertNotRegex(coding, r"50\s*行|stars\s*>?\s*1000")

    def test_incremental_refinement_requires_evidence_not_model_accumulation(self) -> None:
        method = read_rule("rules/incremental-refinement.md")
        coding = read_rule("rules/coding-principles.md")
        case_q = read_rule("eval/case-q-incremental-refinement.md")

        for phrase in (
            "当前行为",
            "目标行为",
            "差异",
            "用户使用“补充”“另外”等词",
            "只是检查信号，不足以证明应归并",
            "共享同一职责、业务不变量或变化原因",
            "只有代码、Schema、契约或测试证明存在状态集合和状态转换约束时",
            "不得因增加一个条件、异常路径或功能说明就引入状态枚举",
        ):
            self.assertIn(phrase, method)
        self.assertIn("实体、名称、分支或措辞相似本身不构成归并依据", coding)
        self.assertIn("不要求特定字段、函数、状态表示、验证层或状态机", case_q)
        self.assertIn("不补造状态机", case_q)

    def test_logic_test_requirements_are_conditioned_on_existing_contracts(self) -> None:
        for path in ("mini/agent.md", "lite/agent.md"):
            with self.subTest(path=path):
                policy = read_rule(path)
                self.assertIn("逻辑改动补", policy)
                self.assertIn("只有证据确认存在状态机或状态转换契约时", policy)
                self.assertIn("不得为满足测试分类而补造状态机", policy)
                self.assertNotIn("状态机全覆盖，含非法转换", policy)

    def test_case_n_documents_state_gate_evaluation_protocol(self) -> None:
        case_n = read_rule("eval/case-n-operational-criteria.md")
        eval_readme = read_rule("eval/README.md")
        self.assertIn("### 状态与继续门禁（四版通用）", case_n)
        for phrase in ("文字假进展变体", "统计采样变体", "验证未完成的交付变体", "预算与恢复"):
            self.assertIn(phrase, case_n)
        self.assertIn("### 状态门禁的 A/B 评测", eval_readme)


if __name__ == "__main__":
    unittest.main()
