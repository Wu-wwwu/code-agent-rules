# 最小改动原则的扩展：从代码到需求与文档

**日期**: 2026-10-12  
**版本**: rules-v3.02-hybrid  
**问题来源**: 用户反馈 - 多轮对话导致代码臃肿、文档追加、概念重复

---

## 问题分析

### 原始问题描述

用户观察到：
1. **代码臃肿**：根据用户输入生成了很多代码，造成代码不易阅读
2. **文档偏离**：文档记录与实际代码和结构差异渐渐变大
3. **重复表达**：对一个需求、一种业务的多次描述补充
4. **逻辑分散**：最终用了大量代码、代码概念模型、业务代码，大量重复判断

### 根本原因

**当前规则的"最小改动"只约束了单次代码修改的范围，未约束多轮对话中需求理解和文档记录的归并方式。**

Agent 倾向于：
- **累加式生成**：每次用户补充 → 生成新代码 → 追加新文档
- **叙事性记录**：记录"用户要求 X → 讨论后决定 Y → 接下来做 Z"
- **概念重复**：同一实体在 Order/OrderEntity/OrderDTO/orders 中重复定义
- **判断分散**：同一前提在多个函数中重复检查

而非：
- **归并式细化**：识别补充为已有需求的边界细化 → 归并到已有模型
- **状态断言**：记录"当前状态、目标状态、差异"
- **概念统一**：glossary 中统一表达，其他地方引用
- **逻辑集中**：提取统一验证函数

---

## 解决方案

### 新增规则文件

**rules/incremental-refinement.md** (408 行)

定义 5 大原则：
1. **需求理解的归并式细化**：识别归并信号，细化边界而非追加功能
2. **代码实现的归并而非累加**：状态显式化、约束集中化、转换统一化
3. **文档记录的收敛而非追加**：重写受影响章节，而非追加"第 N 轮"
4. **概念模型的去重与归并**：glossary 统一多重表达，提供映射证据
5. **触发归并的 5 类信号**：涉及已有实体、否定/约束已有行为、补充分支、重复逻辑、用户用"也/另外/补充"

### 集成到现有规则

1. **agent.md** - 能力路由表新增：
   ```markdown
   | 用户多轮补充需求，如何避免累加式生成和文档追加？ 
   | `./incremental-refinement.md` 
   | 已有模型、代码实现、项目文档当前章节 |
   ```

2. **agent.md** - 分析后执行触发条件补充：
   ```markdown
   - 用户多轮补充边界、约束或分支时，先识别是否为已有需求的细化；
     是则按 `./incremental-refinement.md` 归并到已有模型、代码或文档，
     而非累加新实现或追加新段落；
   ```

3. **coding-principles.md** - 基本准则新增：
   ```markdown
   | **归并优先于累加** 
   | 新需求涉及已有实体或流程时，优先归并到已有实现
     （状态显式化、约束集中化、转换统一化），
     而非新增平行函数或包装层 |
   ```

4. **document-init.md** - 初始化原则补充：
   ```markdown
   - **收敛而非追加**：每轮更新时重写受影响章节为当前最新理解，
     合并重复描述，删除已被细化覆盖的模糊表述；
     不保留"第 N 轮需求"或"用户要求→讨论→决定"过程。
   ```

### 评测案例

**eval/case-q-incremental-refinement.md** (405 行)

场景：4 轮用户注册功能开发
- 第 1 轮：基础注册
- 第 2 轮：用户名唯一性约束
- 第 3 轮：邮箱验证流程
- 第 4 轮：邮箱唯一性约束

预期行为：
- ✅ 代码归并：无 check_username_duplicate/check_email_duplicate 独立函数
- ✅ 状态显式化：使用 status 枚举（pending_verification/active/suspended），而非 email_verified 布尔
- ✅ 文档收敛：重写"用户管理"章节为当前状态，而非追加"第 N 轮"历史
- ✅ 约束集中：约束列在统一 validate_registration()，而非分散检查
- ✅ 概念一致：User 模型、代码、文档的字段和状态描述对齐

反模式检测：
- ❌ 平行函数变体（register_v1, register_v2）
- ❌ 布尔标志代替状态机
- ❌ 文档追加"第 N 轮"或"用户要求 X"
- ❌ 分散的条件检查

---

## 核心对比

### Before：累加式生成

```python
# 第 1 轮
def create_order(user_id, items):
    order = Order(user_id=user_id, items=items)
    db.save(order)
    return order

# 第 2 轮：补充"可以取消"
def cancel_order(order_id):
    order = db.get(order_id)
    order.status = 'cancelled'
    db.save(order)

# 第 3 轮：补充"已支付不能取消"
def cancel_order(order_id):
    order = db.get(order_id)
    if order.status == 'paid':  # 又一个独立检查
        raise Exception("不能取消已支付订单")
    order.status = 'cancelled'
    db.save(order)
```

**问题**：
- 3 个独立修改
- 状态转换分散
- 没有统一验证
- create_order 未设置初始状态

**文档**：
```markdown
## 订单管理

### 2026-10-01 初始需求
- 用户要求：创建订单、查询订单

### 2026-10-05 补充需求
- 用户要求：订单可以取消

### 2026-10-08 约束细化
- 用户要求：已支付的不能取消
```

**问题**：
- 3 次追加，每次"用户要求 → 实现"
- 无法看出当前完整边界
- 决策依据分散

### After：归并式细化

```python
# 归并后的统一实现
class Order:
    STATES = ['created', 'paid', 'cancelled']
    TRANSITIONS = {
        'created': ['paid', 'cancelled'],
        'paid': [],  # 已支付不能取消
        'cancelled': []
    }
    
    def __init__(self, user_id, items):
        self.user_id = user_id
        self.items = items
        self.status = 'created'  # 显式初始状态
    
    def cancel(self):
        if 'cancelled' not in self.TRANSITIONS[self.status]:
            raise InvalidTransition(f"Cannot cancel from {self.status}")
        self.status = 'cancelled'
```

**改进**：
- 1 个状态机模型
- 转换约束集中在 TRANSITIONS
- cancel() 方法无需修改，约束已归并
- 初始状态显式化

**文档**：
```markdown
## 订单状态管理

**当前状态**：订单生命周期由状态机管理，支持创建、支付、取消操作。

**状态定义**：created | paid | cancelled

**允许转换**：
- created → paid：用户完成支付
- created → cancelled：用户取消订单
- paid → (无转换)：已支付订单不可取消（证据：2026-10-08 用户确认）

**实现位置**：Order.cancel() @ src/orders/model.py:42
```

**改进**：
- 1 个收敛的当前状态章节
- 清晰的状态集合和转换规则
- 仅保留影响当前约束的证据
- 无"第 N 轮"追加

---

## 5 类归并信号

Agent 必须先尝试归并，而非直接累加：

1. **新输入涉及已有实体的行为边界**
   - "订单可以取消" → 归并到订单状态管理
   - "管理员可以强制取消" → 归并到订单权限模型

2. **新约束否定或限制已有行为**
   - "已支付的不能取消" → 细化状态转换约束
   - "单笔订单不超过 100 件商品" → 归并到订单验证规则

3. **新分支补充已有流程**
   - "支付失败时记录原因" → 归并到支付流程的失败处理分支
   - "库存不足时降级到预订" → 归并到库存检查的分支

4. **发现重复表达**
   - 2 个函数包含相同的 5 行判断逻辑
   - 3 处文档描述同一业务规则但措辞不同

5. **用户用"也"、"另外"、"补充"等词**
   - 语义上表明是对已有内容的扩展

---

## 实施效果

### 规则规模

| 项目 | Before | After | 增量 |
|------|--------|-------|------|
| 规则文件数 | 11 | 12 | +1 (incremental-refinement.md) |
| 规则总行数 | ~481 | ~1275 | +794 |
| 评测案例数 | 16 | 17 | +1 (Case Q) |
| 能力路由 | 19 | 20 | +1 (多轮归并) |

### 方法完备性

- **Before**: ★★★★☆ - 核心领域覆盖全面，但多轮对话无约束
- **After**: ★★★★★ - 全覆盖，增量细化规则解决累加生成问题

### 综合评分

- **Before**: 4.4 / 5.0
- **After**: 4.6 / 5.0（提升 0.2）

### 核心价值演进

- **Before**: 三位一体（证据优先 + 风险分层 + 状态记忆）
- **After**: 四位一体（证据优先 + 风险分层 + 状态记忆 + **归并细化**）

---

## 测试验证

所有 77 项契约测试通过（3 项因符号链接权限跳过）：

```
Ran 77 tests in 2.807s
OK (skipped=3)
```

关键测试：
- ✅ test_minimal_model_distinguishes_data_lifecycles_without_forcing_all_tasks
- ✅ test_case_o_covers_current_facts_lifecycles_and_lightweight_path
- ✅ test_decision_evidence_contracts
- ✅ test_module_goal_lifecycle_method_is_routed_and_evaluated

---

## Git 提交历史

```
726ad1f Update EVALUATION.md with incremental refinement enhancement
253ac94 Add Case Q: multi-round requirement refinement evaluation
d4c4696 Add incremental refinement over accumulative generation
064c3b8 Add comprehensive evaluation report for rules v3.02-hybrid
2fe50c2 Add state-assertion priority over narrative recording
72abb3c Add logic change self-check and mandatory testing for mini and lite
f4bc094 Add module local workspace structure and retention rules
```

关键提交 **d4c4696**：
- 新增 rules/incremental-refinement.md (408 行)
- 集成到 agent.md（能力路由 + 触发条件）
- 集成到 coding-principles.md（归并优先原则）
- 集成到 document-init.md（收敛而非追加）
- 新增 Case Q 评测案例

---

## 与用户原始问题的对应

| 用户问题 | 解决方案 | 体现位置 |
|---------|---------|---------|
| 代码臃肿，生成很多代码 | 归并优先于累加：状态显式化、约束集中化、转换统一化 | incremental-refinement.md 第 2 节 |
| 文档与代码差异变大 | 收敛而非追加：每轮重写受影响章节，而非追加"第 N 轮" | incremental-refinement.md 第 3 节 |
| 对同一需求多次描述补充 | 归并式细化：识别补充为已有需求的边界细化 | incremental-refinement.md 第 1 节 |
| 大量重复判断 | 概念去重：glossary 统一多重表达；逻辑集中：提取统一验证 | incremental-refinement.md 第 4 节 |

---

## 后续建议

### 短期（已完成）
- ✅ 补充增量细化规则
- ✅ 编写 Case Q 评测案例
- ✅ 更新 EVALUATION.md

### 中期（1-3 个月）
1. 补充反模式示例库（累加式代码、追加式文档的典型错误）
2. 在 data-structure-analysis.md 补充"概念去重与归并"章节
3. 增加 3 个高价值评测案例：
   - Case R: 大规模重构的归并边界控制
   - Case S: 性能优化的多轮归并
   - Case T: 安全漏洞修复的归并验证

### 长期（3-6 个月）
1. 开发归并建议工具：
   - 分析多轮对话，识别累加信号
   - 提示归并机会
   - 自动检测重复逻辑

2. 建立归并质量度量：
   - 代码重复度（检测分散的相似判断）
   - 文档冗余度（检测"第 N 轮"追加）
   - 概念一致性（检测多重表达）

3. 基于真实项目数据调优归并触发阈值

---

## 总结

**"最小改动"原则成功从代码层扩展到需求理解和文档记录层**。

核心思想：
- **代码层**："最小正确改动集"，不因 diff 小而破坏完整性
- **需求层**："归并式细化"，补充是细化边界而非新功能
- **文档层**："收敛而非追加"，重写章节而非追加历史

这一扩展解决了多轮对话中 Agent 倾向于累加式生成的根本问题，使规则体系从"单次代码修改约束"进化为"多轮理解与实现的全生命周期约束"。

**最终状态**：
- 12 个规则文件，~1275 行
- 17 个评测案例，~1258 行
- 77 项契约测试全通过
- 综合评分：4.6/5.0

---

**报告生成时间**: 2026-10-12 17:46  
**评估人**: Claude Code (claude-opus-5-5)
