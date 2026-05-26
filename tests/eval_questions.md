# SynHub 知识库评测问题集

基于 11 个分类、93 篇文档设计，覆盖 5 种检索能力维度。

---

## 一、单文档精准命中（30 题）

> 每题应命中 1-2 篇特定文档，考察关键词精确匹配能力。

| # | 问题 | 预期命中分类 | 关键检索词 |
|---|------|-------------|-----------|
| 1 | `set_clock_gating_style` 命令的 `-sequential_cell` 参数怎么用？ | 04-时序优化 | clock gating, sequential_cell, set_clock_gating_style |
| 2 | DC 综合中 `compile_ultra` 和 `compile` 的区别是什么？ | 01-综合基础 / 02-TCL脚本 | compile_ultra, compile, DC |
| 3 | 如何在 SDC 中定义 generated clock？ | 03-时序约束 | generated clock, SDC, create_generated_clock |
| 4 | Genus 的 `syn_generic` 和 `syn_opt` 阶段分别做什么？ | 01-综合基础 | Genus, syn_generic, syn_opt |
| 5 | 什么是 multicycle path？SDC 中怎么约束？ | 03-时序约束 | multicycle path, SDC, set_multicycle_path |
| 6 | FSM 状态编码用 one-hot 还是 binary 好？ | 05-面积优化 | FSM encoding, one-hot, binary |
| 7 | UPF 文件中 `create_power_domain` 的语法是什么？ | 06-功耗优化 | UPF, create_power_domain, power domain |
| 8 | DFT scan chain 插入后怎么验证连通性？ | 07-DFX | DFT, scan chain, 连通性 |
| 9 | DC 输出网表的格式是什么？verilog 还是 ddc？ | 08-后端接口 | DC, netlist, verilog, ddc |
| 10 | `report_timing` 命令中 `-max_paths` 参数的作用？ | 02-TCL脚本 / 04-时序优化 | report_timing, max_paths |
| 11 | 什么是 false path？为什么要设 false path？ | 03-时序约束 | false path, set_false_path |
| 12 | clock tree synthesis (CTS) 在综合阶段还是后端做？ | 04-时序优化 / 08-后端接口 | CTS, clock tree synthesis |
| 13 | `report_area` 输出的组合逻辑面积和时序逻辑面积怎么看？ | 05-面积优化 | report_area, combinational, sequential |
| 14 | multi-Vt 综合中 HVT/SVT/LVT 单元的选择策略？ | 06-功耗优化 | multi-Vt, HVT, SVT, LVT |
| 15 | BIST (Built-In Self Test) 的配置步骤是什么？ | 07-DFX | BIST, 配置, DFT |
| 16 | DEF 文件和 LEF 文件在后端流程中的作用？ | 08-后端接口 | DEF, LEF, 后端 |
| 17 | DRC violation 怎么在综合阶段提前修复？ | 09-常见问题 | DRC, violation, fix |
| 18 | LVS 报告中 "net mismatch" 是什么意思？ | 09-常见问题 | LVS, net mismatch |
| 19 | DC 中 `set_input_delay` 和 `set_output_delay` 怎么配合时钟定义？ | 03-时序约束 | input_delay, output_delay, clock |
| 20 | 什么是 clock gating？它降低的是静态功耗还是动态功耗？ | 04-时序优化 / 06-功耗优化 | clock gating, 动态功耗, power |
| 21 | Genus 中怎么看 QoR 报告？ | 01-综合基础 | Genus, QoR, report |
| 22 | SDC 中 `set_clock_groups -asynchronous` 和 `-logically_exclusive` 的区别？ | 03-时序约束 | clock_groups, asynchronous, logically_exclusive |
| 23 | 综合后 timing 违例但 area 已经超了，怎么权衡？ | 04-时序优化 / 05-面积优化 | timing, area, 权衡 |
| 24 | UPF 中 isolation cell 的插入时机和方式？ | 06-功耗优化 | UPF, isolation cell, 插入 |
| 25 | scan chain 的 ordering 对测试覆盖率有影响吗？ | 07-DFX | scan chain, ordering, 测试覆盖率 |
| 26 | 综合到布局布线的交接需要检查哪些项目？ | 08-后端接口 | 综合, P&R, 交接, checklist |
| 27 | `compile_ultra -area` 会牺牲时序吗？ | 04-时序优化 / 05-面积优化 | compile_ultra, area, timing |
| 28 | 什么是 level shifter？在什么场景下需要？ | 06-功耗优化 | level shifter, 电平转换 |
| 29 | DC 中怎么设置 operating conditions？ | 03-时序约束 | operating conditions, set_operating_conditions |
| 30 | 综合失败报 "unresolved references" 是什么原因？ | 09-常见问题 | unresolved references, 综合失败 |

---

## 二、多文档综合回答（20 题）

> 每题应命中 3+ 篇不同分类的文档，考察 RRF 融合和跨领域检索能力。

| # | 问题 | 预期命中分类 | 考察能力 |
|---|------|-------------|---------|
| 1 | 从 RTL 到 GDS 的完整流程中，综合阶段需要做哪些关键决策？ | 01 + 02 + 03 + 04 + 08 | 跨 5 个分类的流程串联 |
| 2 | 低功耗设计中，UPF、clock gating、multi-Vt 三者如何协同工作？ | 04 + 06 | 时序优化 × 功耗优化交叉 |
| 3 | DC 和 Genus 在处理时序约束时有哪些异同？ | 01 + 02 + 03 | 工具对比 + 脚本 + 约束 |
| 4 | 一个模块综合后 area 超标、timing 违例、DRC violation 同时存在，怎么按优先级处理？ | 04 + 05 + 09 | 优化策略 + 常见问题排查 |
| 5 | DFT 插入对综合后网表的时序和面积有什么影响？怎么评估？ | 04 + 05 + 07 + 08 | DFT × 时序 × 面积 × 后端 |
| 6 | 时钟树综合（CTS）前后，时序约束需要做哪些调整？ | 03 + 04 + 08 | 约束 + 优化 + 后端交接 |
| 7 | 如何搭建一个可复用的 DC 综合脚本框架？需要包含哪些模块？ | 01 + 02 + 03 | 基础 + 脚本 + 约束 |
| 8 | 跨时钟域设计中，false path、multicycle path、clock groups 怎么配合使用？ | 03 + 04 | 约束策略 + 时序优化 |
| 9 | 综合报告中哪些指标最关键？怎么从报告中定位问题？ | 01 + 04 + 05 + 06 | 报告解读 + 多维度分析 |
| 10 | 从综合到后端，网表质量怎么评估？哪些指标需要重点关注？ | 01 + 08 + 10 | QoR + 后端 + 实战经验 |
| 11 | Genus 的 incremental synthesis 在什么场景下使用效果最好？ | 01 + 04 + 10 | Genus 特性 + 时序 + 案例 |
| 12 | 多电压域设计中，综合阶段需要处理哪些与后端交接相关的问题？ | 06 + 08 + 11 | 功耗 + 后端 + 红绿区 |
| 13 | 如何在综合阶段同时优化 timing、area 和 power？三者的 trade-off 策略？ | 04 + 05 + 06 | 三目标优化 |
| 14 | 约束文件（SDC）的质量对综合结果有多大影响？常见约束错误有哪些？ | 03 + 09 | 约束 + 常见问题 |
| 15 | 一个新模块从零开始综合，完整的流程和检查清单是什么？ | 01 + 02 + 03 + 09 + 10 | 全流程串联 |
| 16 | 综合中遇到 "cannot resolve module" 和 "unconnected port" 分别怎么处理？ | 02 + 09 | TCL 脚本 + 常见问题 |
| 17 | clock gating 插入后 timing 违例，是因为门控单元延迟还是约束问题？怎么排查？ | 03 + 04 + 09 | 约束 + 优化 + 排查 |
| 18 | DC 和 Genus 在功耗优化方面各自有哪些独特能力？ | 01 + 06 | 工具对比 + 功耗 |
| 19 | 从综合报告看，哪些指标预示着后端布局布线会出问题？ | 01 + 08 + 10 | 综合报告 + 后端预判 |
| 20 | DRC fix 和 timing fix 的优先级怎么定？两者会互相影响吗？ | 04 + 05 + 09 | 优化 + 面积 + 问题排查 |

---

## 三、语义近似问题（20 组）

> 每组 2-3 个问题用不同表述问同一件事，考察语义检索鲁棒性。

| 组 | 问题 A | 问题 B | 问题 C | 核心语义 |
|----|--------|--------|--------|---------|
| 1 | clock gating 是什么？ | 时钟门控技术的原理？ | 门控时钟怎么降低功耗？ | clock gating 原理 |
| 2 | 怎么写 DC 综合脚本？ | Design Compiler 的 TCL 脚本模板？ | DC 脚本的基本框架是什么？ | DC 脚本编写 |
| 3 | SDC 约束怎么写？ | 时序约束文件格式？ | Synopsys Design Constraints 语法？ | SDC 语法 |
| 4 | Genus 和 DC 哪个好？ | Cadence Genus 对比 Synopsys DC？ | 选 DC 还是 Genus 做综合？ | DC vs Genus |
| 5 | 面积太大了怎么办？ | 怎么减小综合后的面积？ | 面积优化有哪些方法？ | 面积优化 |
| 6 | 功耗报告怎么看？ | power report 的关键字段？ | 综合后功耗数据怎么分析？ | 功耗报告解读 |
| 7 | DFT 怎么插？ | scan chain 的插入流程？ | design for testability 的实现步骤？ | DFT 插入 |
| 8 | 网表格式有哪些？ | netlist 用 verilog 还是 ddc？ | 综合输出什么格式给后端？ | 网表输出格式 |
| 9 | timing 违例怎么修？ | 时序不满足怎么优化？ | setup/hold violation 的修复方法？ | 时序修复 |
| 10 | 什么是多周期路径？ | multicycle path 的约束方法？ | 数据路径跨越多个时钟周期怎么约束？ | multicycle path |
| 11 | level shifter 是什么？ | 电平转换器的作用？ | 不同电压域之间怎么传信号？ | level shifter |
| 12 | isolation cell 怎么插？ | 隔离单元的实现方式？ | power domain 之间的隔离怎么处理？ | isolation cell |
| 13 | DRC 报告怎么修？ | design rule violation 怎么解决？ | 综合后 DRC error 的处理方法？ | DRC fix |
| 14 | LVS 报错怎么办？ | layout vs schematic 不匹配？ | 网表和版图不一致怎么排查？ | LVS 排查 |
| 15 | FSM 编码选什么？ | finite state machine 的编码方式？ | 状态机用 binary 还是 one-hot？ | FSM encoding |
| 16 | 什么是 false path？ | 虚假路径怎么设？ | 不需要检查时序的路径怎么标记？ | false path |
| 17 | CTS 在哪里做？ | clock tree synthesis 是综合还是后端？ | 时钟树综合的流程是什么？ | CTS 流程 |
| 18 | UPF 文件怎么写？ | Unified Power Format 语法？ | 低功耗设计的电源意图文件？ | UPF 语法 |
| 19 | 综合失败怎么排查？ | synthesis error 的常见原因？ | DC/Genus 综合报错怎么处理？ | 综合失败排查 |
| 20 | 怎么评估综合质量？ | QoR 报告怎么看？ | 综合结果的好坏怎么判断？ | QoR 评估 |

---

## 四、跨域隐含关联（15 题）

> 问题不直接包含分类关键词，但答案需要综合多篇文档。考察 RRF 对隐含语义的捕捉能力。

| # | 问题 | 隐含关联 | 预期命中 |
|---|------|---------|---------|
| 1 | 一个设计在仿真中功能正确，但综合后功能异常，可能是什么原因？ | RTL → 综合映射问题，可能是约束或综合选项导致 | 02 + 03 + 09 |
| 2 | 后端反馈说综合网表的 congestion 很严重，前端能做什么？ | 综合阶段的 wireload model、面积控制影响后端布线 | 05 + 08 + 10 |
| 3 | 项目要求芯片功耗低于 50mW，综合阶段怎么分阶段达成？ | 功耗目标分解到 clock gating、multi-Vt、power domain | 04 + 06 + 10 |
| 4 | 团队新成员总是写错 SDC，有什么系统性的检查方法？ | 约束语法检查、常见错误模式、工具验证 | 03 + 09 |
| 5 | 一个 IP 需要在两个不同电压的项目中复用，综合脚本怎么改？ | 多电压域适配、operating conditions、UPF | 03 + 06 + 08 |
| 6 | 综合后网表的 flip-flop 数量比 RTL 仿真时多了很多，为什么？ | clock gating、pipeline 插入、retiming 等综合优化 | 04 + 05 |
| 7 | 时序收敛后 area 又超了，有没有不牺牲 timing 的降面积方法？ | 资源共享、逻辑重组、don't touch 属性 | 04 + 05 |
| 8 | 工具升级后综合结果变差了，怎么定位是脚本问题还是工具问题？ | 版本差异、脚本兼容性、QoR 对比方法 | 01 + 09 + 10 |
| 9 | 跨时钟域的 CDC 问题能在综合阶段发现吗？ | CDC 检查工具、综合约束、静态分析 | 03 + 07 + 09 |
| 10 | DFT 插入后原来 timing met 的路径变违例了，正常吗？ | DFT 对时序的影响、scan insert 后重综合 | 04 + 07 + 09 |
| 11 | 综合脚本中 `set_dont_touch` 用多了会有什么副作用？ | don't touch 影响优化空间、面积和时序 | 02 + 04 + 05 |
| 12 | 红区和绿区的综合环境配置有什么差异需要注意？ | 区域隔离、数据同步、配置差异 | 11 + 01 |
| 13 | 综合结果和后端 STA 结果差异很大，哪个更可信？ | 综合用 wireload model 估计 vs 后端实际寄生参数 | 01 + 08 + 10 |
| 14 | 一个模块综合时间特别长（>2小时），怎么优化综合脚本提高效率？ | 脚本优化、compile 策略、层次化综合 | 02 + 04 + 10 |
| 15 | 工具报 "max transition violation" 和 "max capacitance violation" 分别意味着什么？怎么修？ | DRC 约束、驱动能力、buffer 插入 | 03 + 04 + 09 |

---

## 五、边界与反例（8 题）

> 考察知识库对模糊查询、空结果、超范围问题的处理能力。

| # | 问题 | 预期行为 | 考察点 |
|---|------|---------|--------|
| 1 | 布局布线怎么做？ | 应回答"超出综合知识库范围"或给出有限信息 | 范围边界 |
| 2 | Verilog 语法教程 | 应说明知识库侧重综合而非 RTL 编写 | 领域边界 |
| 3 | Python 怎么调用 DC？ | 可能部分相关（脚本自动化），但不完全在范围内 | 交叉领域 |
| 4 | 综合工具license不够用怎么办？ | 超出技术范围，应说明 | 非技术问题 |
| 5 | DC 和 Genus 哪个市场占有率高？ | 可能无直接答案，应如实说明 | 商业信息边界 |
| 6 | FPGA 综合和 ASIC 综合的区别？ | 应说明知识库侧重 ASIC 综合 | 平台边界 |
| 7 | 什么是 STA？它和综合有什么关系？ | 应能回答部分（综合中的 timing analysis） | 相关但不完全覆盖 |
| 8 | 芯片功耗的计算公式是什么？ | 可能有部分答案（动态功耗 = αCV²f） | 理论知识边界 |

---

## 附录：问题设计原则

### 关键检索词覆盖

以下高频检索词每类至少出现 3 次：

| 分类 | 核心检索词 |
|------|-----------|
| 01-综合基础 | DC, Genus, compile, QoR, 综合流程 |
| 02-TCL脚本 | TCL, script, 命令, 模板 |
| 03-时序约束 | SDC, clock, I/O delay, multicycle, false path |
| 04-时序优化 | timing, setup, hold, clock gating, critical path |
| 05-面积优化 | area, resource sharing, FSM, encoding |
| 06-功耗优化 | power, UPF, multi-Vt, isolation, level shifter |
| 07-DFX | DFT, scan chain, BIST, ATPG |
| 08-后端接口 | netlist, DEF, LEF, P&R, STA |
| 09-常见问题 | DRC, LVS, error, fix, troubleshoot |
| 10-实战案例 | 案例, 经验, 收敛, 优化过程 |
| 11-红区绿区 | 红区, 绿区, 跨区, 同步, 安全 |

### 中英文混合查询比例

- 纯中文问题：40%（如"时钟门控怎么降低功耗？"）
- 纯英文问题：30%（如"How to use set_clock_gating_style?"）
- 中英混合问题：30%（如"DC 中怎么 set_false_path？"）

### 问题长度分布

- 短问题（<15 字）：20%
- 中等问题（15-40 字）：50%
- 长问题（>40 字）：30%

---

## 使用方法

1. 逐题执行 `search(question)` 并记录召回的文档名
2. 对照"预期命中分类"判断召回是否准确
3. 统计每类问题的召回率、精确率
4. 重点关注"多文档综合"和"语义近似"两组的 RRF 融合效果
5. 输出评测报告，按分类汇总通过率
