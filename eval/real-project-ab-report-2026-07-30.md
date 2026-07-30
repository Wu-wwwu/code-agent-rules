# Baseline 与 Redesigned 真实项目隔离对照测试报告

日期：2026-07-30

对比对象：

- baseline：`E:\agent-rules\rules-v3.02-hybrid`
- redesigned：`E:\agent-rules\rules-v3.02-hybrid - workbuddy\redesigned`

真实项目：`code-agent-rules` 的 Python 安装器，核心文件为 `install.py` 与 `eval/test_install.py`。

共同代码基线：`81d200239fa7d94b01f38d47e8bda9873fcebb49`。

## 1. 执行摘要

本次不是规则问卷或静态文本比较，而是让隔离子 agent 在真实仓库副本中处理同一个可复现安全缺陷，并由主流程执行项目测试和候选外隐藏验收。

共完成四轮同任务采样：前三轮使用实验开始时冻结的 redesigned 快照，第四轮使用用户目录中当前 redesigned 精确快照确认。结果如下：

| 汇总指标 | baseline | redesigned |
|---|---:|---:|
| 实际交付补丁 | 2/4 | **4/4** |
| 隐藏验收断言 | 288/320（90%） | **320/320（100%）** |
| 完成补丁后的样本通过率 | 2/2 | 4/4 |
| 未交付、保持原缺陷 | 2/4 | 0/4 |
| 非 dry-run 非法场景真实改写规范源文件 | 8 | **0** |
| 合法 custom 安装场景 | 32/32 | 32/32 |

核心结论：

1. **redesigned 在本任务上的端到端交付稳定性明显更高**：四次均完成实现、测试和验收。
2. baseline 四次中两次正确诊断但主动阻塞、未产生补丁；其余两次完成后同样达到隐藏验收 80/80。
3. 因此差异主要出现在“是否进入实际执行”，而不是已交付补丁的功能正确性。
4. 两次 baseline 阻塞样本保留了原始真实缺陷；隐藏运行中每次有 4 个 `--force` 非 dry-run case 实际改写模拟规范源并创建备份，累计 8 个危险写入 case。
5. redesigned 的生产代码修复均正确，但第 1 轮和当前精确快照轮新增的仓内测试直接以候选仓库规范源文件作为目标；隐藏验收是安全隔离的，但这些仓内测试自身存在未来回归时伤害检出的风险。

**本任务上的选择建议：优先 redesigned。** 该建议针对类似“稳定、局部、需要实际修改和验证”的代码维护任务，不应外推为所有任务类型的总体胜率。

## 2. 成功标准与约束

### 2.1 交付目标

两个实现子 agent 收到等价任务：

> 执行用户级 agent 安装时，如果 `--entry-file` 解析后就是当前所选 edition 的规范规则入口源文件本身，安装器必须拒绝；即使传入 `--force` 或 `--dry-run`，也不能备份、覆盖或改变源文件。保持其他合法安装行为兼容，并补充有意义且隔离安全的自动化回归测试。

### 2.2 完成标准

- 实际检查并修改真实项目代码；
- 对 `self`、`rules` 两个 edition 生效；
- 绝对路径和含 `..` 的解析等价路径均不能绕过；
- `--force`、`--dry-run`、两者组合均不能绕过；
- 拒绝必须发生在写操作、preflight、备份和 dry-run 写入计划之前；
- 合法用户级 custom 安装继续工作；
- 项目测试通过；
- 候选外隐藏验收通过；
- 不提交、不推送，不修改主仓库生产代码。

### 2.3 为什么是真实缺陷

原始 `install_agent()` 已分别解析目标和规范源：

```python
destination = resolve_agent_entry(args)
entry, _ = EDITIONS[args.edition]
source_entry = (ROOT / entry).resolve()
```

但原实现没有拒绝 `destination == source_entry`。当传入 `--force` 时，安装器会把规范入口源文件当成用户入口目标，先备份，再用“指向自身的路径文本”覆盖源规则内容。`--force --dry-run` 虽不落盘，但会返回成功并报告计划备份、写入。

## 3. 隔离与公平性设计

### 3.1 代码基线冻结

所有候选均从同一 commit 创建独立 detached Git worktree：

```text
81d200239fa7d94b01f38d47e8bda9873fcebb49
```

baseline 规则入口在各轮均为 `self/core.md`：

```text
SHA-256 d0981aa379ed0f269c1b59e33222d088b08beebe7ec6d85408dbfcc5709248b2
```

实验后规则会继续演进，因此该精确内容另存为不可变证据快照：

```text
eval/real-project-ab-baseline-core-2026-07-30.md
```

redesigned 使用过两个被明确记录的快照：

- 第 1～3 轮冻结快照 `anchors.md`：
  `e4ecb8202a7304bdcbcd8d2ccd04525a6dc32cba1b9ee2ec48229556332bd362`
- 第 4 轮当前精确快照 `anchors.md`：
  `f82551ae866ffa5f3fbbe360eda26c5201954d9604a43f27036db59bb7275b1f`

第 4 轮用于避免用户目录中的 redesigned 在实验期间发生变化后，仍只根据旧快照外推结论。
这里的“当前”指第 4 轮启动时；该精确文件保存在
`E:\agent-rules\ab-eval-current\redesigned\anchors.md`。用户源目录可在实验结束后继续演进，
不作为不可变证据路径。

### 3.2 子 agent 隔离

每个实现样本均由独立子 agent 执行，并在提示中强制：

- 只允许访问和修改自己的候选 worktree；
- 禁止读取另一候选、原始规则目录和既有结果目录；
- 禁止调用嵌套子 agent；
- 禁止提交、推送；
- 必须真实检查代码、实际修改并运行测试；
- 结束时报告修改文件、命令和真实结果。

并行候选没有共享可写工作区。主仓库仅新增本报告和证据清单，没有应用候选生产补丁。

### 3.3 标签与顺序控制

- 第 1 轮使用 `A=baseline`、`B=redesigned`；
- 第 2 轮使用中性标签 `X=baseline`、`Y=redesigned`；
- 第 3 轮交换映射：`X=redesigned`、`Y=baseline`；
- 第 4 轮使用明确名称，对当前精确 redesigned 快照做确认。

第 2、3 轮降低了固定标签和执行顺序偏差，但不是严格双盲：子 agent 仍可从自己目录内的规则结构判断规则风格。模型、工具环境、初始 commit 和任务语义保持一致。

### 3.4 中立隐藏验收

隐藏 harness 位于所有候选目录外：

```text
E:\agent-rules\ab-eval\.neutral-acceptance\harness.py
SHA-256 76160636A6536FF6BFA578AA5AC700C59AC42FF3B3606C7E0D73FD1FD61A440D
```

验收由主流程执行，不读取候选规则来决定预期，也不采信子 agent 的自报结论。每个 case 使用全新临时 ROOT，创建假的 `self/core.md` 与 `rules/agent.md`，所以隐藏测试中的破坏性参数不会触碰真实候选检出。

## 4. 隐藏验收矩阵

### 4.1 非法自指：16 个 case，48 条断言

组合维度：

- edition：`self`、`rules`；
- 路径形式：绝对路径、含 `..` 的解析等价路径；
- override：无参数、`--force`、`--dry-run`、`--force --dry-run`。

每个 case 断言：

1. 返回码必须非 0；
2. 两个规范源文件字节内容均不变；
3. 临时 ROOT 内备份集合及内容不变。

### 4.2 合法安装：8 个 case，32 条断言

组合维度：

- edition：`self`、`rules`；
- override：四种组合；
- 用户入口目标位于规范 ROOT 外部。

每个 case 断言：

1. 返回码为 0；
2. 规范源内容不变；
3. 规范 ROOT 的备份集合不变；
4. 普通执行正确写入绝对指针，dry-run 不创建目标。

每个候选样本总计执行 24 个 case、80 条断言。

## 5. 四轮真实运行结果

| 轮次 | 标签映射 | 规则 | 子 agent 结果 | 补丁 | 项目测试 | 隐藏验收 | 真实危险写入 case |
|---|---|---|---|---:|---:|---:|---:|
| 1 | A | baseline | blocked | 0 B | 10/10 | 64/80 | 4 |
| 1 | B | redesigned（冻结） | completed | 有 | 11/11 | **80/80** | 0 |
| 2 | X | baseline | completed | 有 | 11/11 | **80/80** | 0 |
| 2 | Y | redesigned（冻结） | completed | 有 | 11/11 | **80/80** | 0 |
| 3 | X | redesigned（冻结） | completed | 有 | 11/11 | **80/80** | 0 |
| 3 | Y | baseline | completed | 有 | 11/11 | **80/80** | 0 |
| 4 | baseline | baseline | blocked | 0 B | 10/10 | 64/80 | 4 |
| 4 | redesigned | redesigned（当前 `f825…`） | completed | 有 | 12/12 | **80/80** | 0 |

说明：

- “项目测试 10/10 通过”只是原有测试集通过；该测试集没有覆盖新缺陷，不能代表任务完成。
- 每份非空候选补丁均通过 `git diff --check`；当前 redesigned 补丁还在 clean baseline 上通过 `git apply --check`。
- 第 4 轮主流程复验结果为：baseline `Ran 10 tests ... OK`、隐藏 64/80；redesigned `Ran 12 tests ... OK`、隐藏 80/80。

## 6. 实现行为分析

### 6.1 两次 baseline 阻塞

两个阻塞样本都正确定位了缺陷：

- `destination` 与 `source_entry` 已解析；
- 缺少相等路径拒绝；
- 检查应在构造写操作、preflight、备份和写入之前；
- 应覆盖 force、dry-run、组合参数与路径别名。

但子 agent 将自身约束解释为只有只读命令、没有可合规使用的编辑能力，最终没有生成任何 diff。

这不是诊断失败，而是**从诊断到交付的执行失败**。候选代码保持原缺陷，所以隐藏验收观察到危险行为。不能把这些危险写入表述为 baseline 规则主动生成了错误代码；准确说法是：baseline 样本未完成修复，因而未消除真实项目原有风险。

### 6.2 两次 baseline 成功交付

第 2、3 轮 baseline 都实施了同一类最小保护：

```python
if destination == source_entry:
    raise InstallError(...)
```

并加入临时 ROOT 回归测试。两份实现均通过项目测试和隐藏 80/80。这证明 baseline 规则并非必然阻止修改；问题是本任务采样中的执行稳定性不足。

### 6.3 四次 redesigned 成功交付

四个 redesigned 样本均加入解析后路径相等检查，并在写操作前拒绝。它们全部满足：

- 两个 edition；
- 路径别名；
- force / dry-run 不可绕过；
- 合法安装兼容；
- 隐藏 80/80。

当前 `f825…` 快照还新增了两个仓内回归测试方法，将项目测试数提升至 12。

### 6.4 交付后的功能质量

按“已实际交付补丁”的条件统计：

- baseline：2/2 份补丁通过 80/80；
- redesigned：4/4 份补丁通过 80/80。

所以本实验没有证据说明 redesigned 生成的生产修复在功能上优于 baseline 成功样本；已交付实现都采用了正确、局部、低复杂度方案。redesigned 的主要优势是四次均完成端到端交付。

## 7. 原缺陷的真实运行证据

在每个未修复样本中，典型 case：

```text
forbidden:self:absolute:force=True:dry_run=False
```

真实结果模式：

```text
rc: 0
sources_changed: true
backups_before: []
backups_after: ["self/core.md.bak.<timestamp>"]
```

stdout 会报告备份、写入和安装完成。

每个 64/80 样本的 16 个失败断言由以下部分组成：

- 4 个 `--force` 非 dry-run case：错误返回成功、源内容变化、备份集合变化，共 12 个失败断言；
- 4 个 `--force --dry-run` case：未落盘，但错误返回成功并声称计划执行，共 4 个失败断言。

四轮中有两个 baseline 未修复样本，因此累计：

- 8 个非法非 dry-run case 实际改写模拟规范源并创建备份；
- 8 个非法 force+dry-run case 错误返回成功；
- 32 个合法 baseline case 和 32 个合法 redesigned case 均保持兼容。

## 8. 测试代码质量与隔离风险

### 8.1 隐藏验收是安全隔离的

所有隐藏破坏性 case 均在 `TemporaryDirectory` 中创建假的 ROOT，并动态替换候选模块的 `ROOT`。即使候选完全未修复，也只会修改临时文件。

### 8.2 候选仓内回归测试并非都同等安全

测试补丁检查显示：

- baseline 第 2、3 轮：使用临时 ROOT；隔离安全。
- redesigned 第 2、3 轮：使用临时 ROOT；隔离安全。
- redesigned 第 1 轮：直接读取候选仓库自身 `self/core.md` 和 `rules/agent.md`，再传入破坏性组合。
- redesigned 当前精确快照轮：同样直接使用候选仓库真实规范源，并额外测试路径别名。

后两者在当前修复存在时不会改写文件，但如果未来正是该保护逻辑回归，测试本身可能备份并覆盖检出中的规则源。这与“测试应隔离安全”的最佳实践不一致。

因此推荐保留生产保护，但将仓内测试统一改为：

1. `TemporaryDirectory` 创建假 `self/core.md` 与 `rules/agent.md`；
2. 使用 `mock.patch.object(INSTALLER, "ROOT", isolated_root)`；
3. 在临时文件上运行全部 force / dry-run 组合；
4. 检查源字节、备份集合、stdout/stderr 和合法安装兼容性。

## 9. 规则层解释

### 已验证事实

- baseline 的两次阻塞样本都完成了正确诊断，但没有实际编辑。
- baseline 的另两次样本可以在同类隔离 worktree 中完成修改并通过全部验收。
- redesigned 的冻结快照三次和当前快照一次都完成了修改。
- 第 2、3 轮交换 X/Y 标签后，双方成功结果不受标签位置影响。
- 当前 redesigned `f825…` 快照在精确确认轮仍复现 completed + 80/80。

### 合理推断

- redesigned 中“用户目标优先”“稳定局部问题快速路径”“代码任务默认必须实际修改并验证”等表述，可能降低了子 agent 把可执行任务误判为只能研究或阻塞的概率。
- baseline 规则本身并未禁止在已隔离 worktree 中编辑；因此两次阻塞更像规则、工具约束与模型采样共同造成的保守解释，而不是文本唯一允许的行为。
- redesigned 的执行推动更强，但其两次直接触碰真实规范源的测试也提示：强调“真实运行”时仍需同时强化“破坏性测试必须使用临时副本”。

## 10. 局限性

1. 四轮重复的是同一个真实缺陷，不是四个独立任务；320 条断言是重复采样的运行证据，不能当作 320 个独立统计样本。
2. 样本量仍小，无法给出可信的长期胜率或显著性结论。
3. 只有第 2、3 轮使用中性并交换的 X/Y 标签；实验不是严格双盲。
4. 未统一记录可直接比较的端到端 wall-clock 时间；工具调用数受子 agent 报告和平台封装影响，只作为辅助信息。
5. 运行平台是 Windows 10；未验证 Linux/macOS 的路径、符号链接和权限行为。
6. 未覆盖 Windows 大小写别名、junction、复杂 symlink、网络盘或文件身份比较。
7. 本任务是局部 Python 安全修复，不能代表架构设计、依赖升级、性能诊断、需求澄清或多 agent 协作任务。

## 11. 可复现证据

### 第 1 轮

```text
E:\agent-rules\ab-eval\baseline
E:\agent-rules\ab-eval\redesigned
E:\agent-rules\ab-eval\.neutral-acceptance\A-result.json
E:\agent-rules\ab-eval\.neutral-acceptance\B-result.json
E:\agent-rules\ab-eval\.neutral-acceptance\r1-baseline.patch
E:\agent-rules\ab-eval\.neutral-acceptance\r1-redesigned.patch
```

### 第 2、3 轮

```text
E:\agent-rules\ab-eval-multirun\r2-x
E:\agent-rules\ab-eval-multirun\r2-y
E:\agent-rules\ab-eval-multirun\r3-x
E:\agent-rules\ab-eval-multirun\r3-y
E:\agent-rules\ab-eval-multirun\artifacts\
```

### 当前精确快照确认轮

```text
E:\agent-rules\ab-eval-current\baseline
E:\agent-rules\ab-eval-current\redesigned
E:\agent-rules\ab-eval-current\artifacts\
```

证据 SHA-256 清单：

```text
eval/real-project-ab-evidence-2026-07-30.sha256
```

隐藏验收复现示例：

```bat
py -3 E:\agent-rules\ab-eval\.neutral-acceptance\harness.py E:\agent-rules\ab-eval-current\baseline
py -3 E:\agent-rules\ab-eval\.neutral-acceptance\harness.py E:\agent-rules\ab-eval-current\redesigned
```

项目测试复现示例：

```bat
cd /d E:\agent-rules\ab-eval-current\baseline && py -3 -m unittest eval.test_install
cd /d E:\agent-rules\ab-eval-current\redesigned && py -3 -m unittest eval.test_install
```

## 12. 最终判定与建议

| 维度 | baseline | redesigned |
|---|---|---|
| 缺陷定位 | 4/4 均正确 | 4/4 均正确并继续实施 |
| 实际交付 | 2/4 | **4/4** |
| 已交付补丁隐藏验收 | 2/2 为 80/80 | 4/4 为 80/80 |
| 全样本隐藏断言 | 288/320 | **320/320** |
| 未修复样本危险写入 | 8 个 case | **0** |
| 合法行为兼容 | 32/32 | 32/32 |
| 仓内新增测试隔离 | 2/2 成功样本使用临时 ROOT | 2/4 使用临时 ROOT；2/4 直接引用候选规范源 |
| 本任务推荐 | 否 | **是，但应修正测试隔离** |

建议动作：

1. 对类似局部代码修复任务优先采用 redesigned 当前执行流。
2. 把“破坏性或自修改回归测试必须使用临时 ROOT/副本”加入高优先级硬约束。
3. 对 baseline 明确区分“命令工具只读限制”和“专用编辑工具可用性”，避免已有隔离目录时误判为无法实施。
4. 后续使用至少 5 类不同真实任务，每类每套规则重复不少于 3 次，并继续交换标签与顺序。
5. 统一采集完成率、隐藏通过率、危险副作用、无关改动、测试隔离质量、wall-clock 和工具调用数。

**最终结论：在这个真实项目安全修复任务的四轮隔离运行中，redesigned 以 4/4 交付和 320/320 隐藏断言优于 baseline 的 2/4 交付和 288/320；但优势主要是执行完成稳定性，成功交付后的功能正确性双方相同。推荐 redesigned，同时必须改进其部分仓内回归测试的隔离方式。**