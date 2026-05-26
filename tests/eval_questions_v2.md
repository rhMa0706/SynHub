# SynHub 知识库评测问题集 v2

基于 11 个分类、93 篇文档设计，覆盖 5 种检索能力维度。
共 93+ 道问题，含语言比例：纯中文 40% / 纯英文 30% / 中英混合 30%。

---

## 一、精准查询词问题（30 题）

> 每题包含精确的 EDA 术语/命令名，应命中 1-2 篇特定文档。

| # | 问题 | 预期命中分类 | 核心检索词 | 难度 |
|---|------|-------------|-----------|------|
| 1 | `set_clock_gating_style` 命令的 `-sequential_cell` 参数怎么用？ | 04-时序优化 | clock gating, set_clock_gating_style, sequential_cell | easy |
| 2 | DC 中 `compile_ultra` 和 `compile` 的区别是什么？ | 01-综合基础 / 02-TCL脚本 | compile_ultra, compile, Design Compiler | easy |
| 3 | SDC 中如何使用 `create_generated_clock` 定义分频时钟？ | 03-时序约束 | create_generated_clock, SDC, generated clock | medium |
| 4 | Genus 的 `syn_generic` 和 `syn_opt` 阶段分别做什么？ | 01-综合基础 | Genus, syn_generic, syn_opt | easy |
| 5 | `set_multicycle_path` 命令中 `-setup` 和 `-hold` 的关系是什么？ | 03-时序约束 | set_multicycle_path, multicycle path, setup, hold | medium |
| 6 | FSM 编码用 one-hot 还是 binary 对面积和时序的影响？ | 05-面积优化 | FSM encoding, one-hot, binary, FSM | medium |
| 7 | UPF 中 `create_power_domain` 命令的 `-include_scope` 参数含义？ | 06-功耗优化 | UPF, create_power_domain, power domain | hard |
| 8 | DFT scan chain 插入后 `set_scan_path` 的约束方式？ | 07-DFX | DFT, scan chain, set_scan_path | medium |
| 9 | DC 输出 verilog 网表和 ddc 格式各有什么优缺点？ | 08-后端接口 | netlist, verilog, ddc, DC | medium |
| 10 | `report_timing -max_paths 100 -nworst 5` 各参数的含义？ | 02-TCL脚本 / 04-时序优化 | report_timing, max_paths, nworst | easy |
| 11 | `set_false_path -from [get_clocks clkA] -to [get_clocks clkB]` 的作用？ | 03-时序约束 | false path, set_false_path, clock | easy |
| 12 | 综合阶段的 `compile_ultra -timing_driven` 和后端 CTS 有什么关系？ | 04-时序优化 / 08-后端接口 | CTS, timing_driven, compile_ultra | medium |
| 13 | `report_area -hierarchy` 输出中 combinational vs sequential area 怎么看？ | 05-面积优化 | report_area, hierarchy, combinational, sequential | easy |
| 14 | multi-Vt 综合中 `set_multi_vth_constraint` 命令如何设置 HVT 比例？ | 06-功耗优化 | multi-Vt, HVT, set_multi_vth_constraint | hard |
| 15 | BIST controller 的 `bist_mode` 配置有哪些选项？ | 07-DFX | BIST, bist_mode, DFT, ATPG | medium |
| 16 | DEF 文件中 `COMPONENTS` 和 `NETS` section 的格式规范？ | 08-后端接口 | DEF, COMPONENTS, NETS | hard |
| 17 | DRC 中 `max_transition` violation 的修复方法和 `set_max_transition` 约束？ | 09-常见问题 | DRC, max_transition, set_max_transition | medium |
| 18 | LVS 报告中 "pin mismatch" 和 "net mismatch" 的区别？ | 09-常见问题 | LVS, pin mismatch, net mismatch | medium |
| 19 | `set_input_delay -clock clk -max 2.5 [get_ports data_in]` 的时序含义？ | 03-时序约束 | input_delay, set_input_delay, clock | easy |
| 20 | clock gating 的 `integrated_cell` 和 `single_latch` 类型区别？ | 04-时序优化 / 06-功耗优化 | clock gating, integrated_cell, single_latch | medium |
| 21 | Genus 中 `report_qor` 命令输出的关键指标有哪些？ | 01-综合基础 | Genus, QoR, report_qor | easy |
| 22 | `set_clock_groups -asynchronous` 和 `-logically_exclusive` 的语义差异？ | 03-时序约束 | clock_groups, asynchronous, logically_exclusive | medium |
| 23 | DC 中 `compile_ultra -area` 的面积优化策略和副作用？ | 04-时序优化 / 05-面积优化 | compile_ultra, area, timing | medium |
| 24 | `insert_domain` 和 `create_isolation_cell` 在 UPF 中的调用顺序？ | 06-功耗优化 | UPF, isolation cell, insert_domain, create_isolation_cell | hard |
| 25 | scan chain 的 `scan_compression_mode` 对测试时间的影响？ | 07-DFX | scan chain, scan_compression_mode, ATPG | hard |
| 26 | 综合输出的 `.sdc` 文件和 `.ddc` 文件在后端流程中的用途差异？ | 08-后端接口 | SDC, ddc, 后端, P&R | medium |
| 27 | `report_constraint` 命令如何检查 max_capacitance violation？ | 09-常见问题 | report_constraint, max_capacitance, DRC | easy |
| 28 | UPF 中 `set_level_shifter` 的 `-rules` 参数怎么配置？ | 06-功耗优化 | UPF, level shifter, set_level_shifter, rules | hard |
| 29 | DC 中 `set_operating_conditions` 的 `-min_library` 和 `-max_library` 含义？ | 03-时序约束 | operating conditions, set_operating_conditions, library | medium |
| 30 | 综合报 "unresolved references" 时的 `link` 和 `uniquify` 排查流程？ | 09-常见问题 | unresolved references, link, uniquify, 综合失败 | easy |

---

## 二、多文档综合问题（25 题）

> 每题应命中 3+ 篇不同分类的文档，考察 RRF 融合和跨领域检索能力。

| # | 问题 | 预期命中分类 | 核心检索词 | 难度 |
|---|------|-------------|-----------|------|
| 1 | 从 RTL 到 GDS 的完整流程中，综合阶段需要做哪些关键决策？ | 01 + 02 + 03 + 04 + 08 | RTL, GDS, 综合流程, compile | hard |
| 2 | 低功耗设计中，UPF、clock gating、multi-Vt 三者如何协同工作？ | 04 + 06 | UPF, clock gating, multi-Vt, power | hard |
| 3 | DC 和 Genus 在处理时序约束时有哪些异同？ | 01 + 02 + 03 | DC, Genus, SDC, 约束 | hard |
| 4 | 一个模块综合后 area 超标、timing 违例、DRC violation 同时存在，怎么按优先级处理？ | 04 + 05 + 09 | timing, area, DRC, 优化策略 | hard |
| 5 | DFT 插入对综合后网表的时序和面积有什么影响？怎么评估？ | 04 + 05 + 07 + 08 | DFT, timing, area, netlist | hard |
| 6 | 时钟树综合（CTS）前后，时序约束需要做哪些调整？ | 03 + 04 + 08 | CTS, SDC, timing, clock tree | hard |
| 7 | 如何搭建一个可复用的 DC 综合脚本框架？需要包含哪些模块？ | 01 + 02 + 03 | DC, script, TCL, 框架 | medium |
| 8 | 跨时钟域设计中，false path、multicycle path、clock groups 怎么配合使用？ | 03 + 04 | false path, multicycle, clock groups, CDC | hard |
| 9 | 综合报告中哪些指标最关键？怎么从报告中定位问题？ | 01 + 04 + 05 + 06 | QoR, report, timing, power, area | medium |
| 10 | 从综合到后端，网表质量怎么评估？哪些指标需要重点关注？ | 01 + 08 + 10 | netlist, QoR, STA, 后端 | hard |
| 11 | Genus 的 incremental synthesis 在什么场景下使用效果最好？ | 01 + 04 + 10 | Genus, incremental synthesis, timing | medium |
| 12 | 多电压域设计中，综合阶段需要处理哪些与后端交接相关的问题？ | 06 + 08 + 11 | UPF, power domain, 红区, 绿区, P&R | hard |
| 13 | 如何在综合阶段同时优化 timing、area 和 power？三者的 trade-off 策略？ | 04 + 05 + 06 | timing, area, power, trade-off | hard |
| 14 | 约束文件（SDC）的质量对综合结果有多大影响？常见约束错误有哪些？ | 03 + 09 | SDC, 约束错误, 综合失败 | medium |
| 15 | 一个新模块从零开始综合，完整的流程和检查清单是什么？ | 01 + 02 + 03 + 09 + 10 | 综合流程, 检查清单, checklist | medium |
| 16 | 综合中遇到 "cannot resolve module" 和 "unconnected port" 分别怎么处理？ | 02 + 09 | TCL, error, module resolution, 排查 | medium |
| 17 | clock gating 插入后 timing 违例，是因为门控单元延迟还是约束问题？怎么排查？ | 03 + 04 + 09 | clock gating, timing, 违例, 排查 | hard |
| 18 | DC 和 Genus 在功耗优化方面各自有哪些独特能力？ | 01 + 06 | DC, Genus, power, 功耗优化 | medium |
| 19 | 从综合报告看，哪些指标预示着后端布局布线会出问题？ | 01 + 08 + 10 | report, congestion, 后端, P&R | hard |
| 20 | DRC fix 和 timing fix 的优先级怎么定？两者会互相影响吗？ | 04 + 05 + 09 | DRC, timing, fix, 优先级 | medium |
| 21 | 综合脚本中如何统一管理多个模块的约束和脚本？层次化综合怎么做？ | 02 + 03 + 10 | TCL, SDC, 层次化综合, 模块化 | medium |
| 22 | 芯片综合后需要做哪些 signoff 检查？每项检查关注什么？ | 01 + 04 + 05 + 09 | signoff, 检查, timing, DRC, LVS | hard |
| 23 | 综合阶段做 power analysis 需要哪些输入文件？和后端的功耗分析有什么区别？ | 06 + 08 | power analysis, 功耗分析, 输入文件 | medium |
| 24 | 低功耗设计中 isolation cell、level shifter 和 retention register 的插入时机和顺序？ | 06 + 08 + 11 | isolation cell, level shifter, retention register, UPF | hard |
| 25 | 综合后的网表如何和形式验证工具对接？需要准备哪些文件？ | 08 + 09 | 形式验证, netlist, 形式签核 | medium |

---

## 三、语义近似问题（20 组）

> 每组 2-3 个问题用不同表述问同一件事，考察语义检索鲁棒性。
> 标注难度为组内最难问题的难度。

| 组 | 问题 A（中文） | 问题 B（英文） | 问题 C（中英混合） | 核心语义 | 难度 |
|----|---------------|---------------|-------------------|---------|------|
| 1 | clock gating 是什么？ | What is clock gating technology? | 门控时钟怎么降低功耗？ | clock gating 原理 | easy |
| 2 | 怎么写 DC 综合脚本？ | How to write a DC synthesis TCL script? | DC 脚本的基本框架是什么？ | DC 脚本编写 | easy |
| 3 | SDC 约束怎么写？ | What is the SDC constraint syntax? | 时序约束文件格式是什么样的？ | SDC 语法 | easy |
| 4 | Genus 和 DC 哪个好？ | Which is better, Cadence Genus or Synopsys DC? | 选 DC 还是 Genus 做综合？ | DC vs Genus | easy |
| 5 | 面积太大了怎么办？ | How to reduce synthesis area? | 面积优化有哪些方法？ | 面积优化 | easy |
| 6 | 功耗报告怎么看？ | How to read the power report in DC? | 综合后功耗数据怎么分析？ | 功耗报告解读 | medium |
| 7 | DFT 怎么插？ | How to insert DFT scan chains? | design for testability 的实现步骤？ | DFT 插入 | medium |
| 8 | 网表格式有哪些？ | What netlist formats does DC output? | 综合输出什么格式给后端？ | 网表输出格式 | easy |
| 9 | timing 违例怎么修？ | How to fix setup and hold violations? | 时序不满足怎么优化？ | 时序修复 | medium |
| 10 | 什么是多周期路径？ | What is a multicycle path in SDC? | 数据路径跨越多个时钟周期怎么约束？ | multicycle path | medium |
| 11 | level shifter 是什么？ | What is the function of a level shifter cell? | 不同电压域之间怎么传信号？ | level shifter | medium |
| 12 | isolation cell 怎么插？ | How to implement isolation cells in UPF? | power domain 之间的隔离怎么处理？ | isolation cell | medium |
| 13 | DRC 报告怎么修？ | How to fix design rule violations in synthesis? | 综合后 DRC error 的处理方法？ | DRC fix | medium |
| 14 | LVS 报错怎么办？ | What causes LVS mismatch errors? | 网表和版图不一致怎么排查？ | LVS 排查 | medium |
| 15 | FSM 编码选什么？ | What are the trade-offs of FSM encoding schemes? | 状态机用 binary 还是 one-hot？ | FSM encoding | medium |
| 16 | 什么是 false path？ | What is a false path in timing constraints? | 不需要检查时序的路径怎么标记？ | false path | easy |
| 17 | CTS 在哪里做？ | Is clock tree synthesis done during synthesis or P&R? | 时钟树综合的流程是什么？ | CTS 流程 | medium |
| 18 | UPF 文件怎么写？ | How to write a Unified Power Format file? | 低功耗设计的电源意图文件怎么写？ | UPF 语法 | hard |
| 19 | 综合失败怎么排查？ | How to debug synthesis errors in DC/Genus? | DC/Genus 综合报错怎么处理？ | 综合失败排查 | medium |
| 20 | 怎么评估综合质量？ | How to evaluate synthesis QoR? | 综合结果的好坏怎么判断？ | QoR 评估 | easy |

---

## 四、隐含关联问题（15 题）

> 问题不直接包含分类关键词，但答案需要多篇文档。考察 RRF 对隐含语义的捕捉能力。

| # | 问题 | 隐含关联 | 预期命中分类 | 核心检索词 | 难度 |
|---|------|---------|-------------|-----------|------|
| 1 | 一个设计在仿真中功能正确，但综合后功能异常，可能是什么原因？ | RTL 综合映射问题、约束或综合选项导致功能变化 | 02 + 03 + 09 | 综合失败, SDC, 功能异常 | hard |
| 2 | 后端反馈说综合网表的 congestion 很严重，前端能做什么？ | wireload model、面积控制影响后端布线 | 05 + 08 + 10 | congestion, wireload, area | hard |
| 3 | 项目要求芯片功耗低于 50mW，综合阶段怎么分阶段达成？ | 功耗目标分解到 clock gating、multi-Vt、power domain | 04 + 06 + 10 | 功耗, power, clock gating, multi-Vt | hard |
| 4 | 团队新成员总是写错 SDC，有什么系统性的检查方法？ | 约束语法检查、常见错误模式、工具验证 | 03 + 09 | SDC, 约束检查, 报错 | medium |
| 5 | 一个 IP 需要在两个不同电压的项目中复用，综合脚本怎么改？ | 多电压域适配、operating conditions、UPF | 03 + 06 + 08 | 多电压, UPF, operating conditions | hard |
| 6 | 综合后网表的 flip-flop 数量比 RTL 仿真时多了很多，为什么？ | clock gating、pipeline 插入、retiming 等综合优化 | 04 + 05 | flip-flop, retiming, clock gating | medium |
| 7 | 时序收敛后 area 又超了，有没有不牺牲 timing 的降面积方法？ | 资源共享、逻辑重组、don't touch 属性 | 04 + 05 | timing, area, resource sharing | hard |
| 8 | 工具升级后综合结果变差了，怎么定位是脚本问题还是工具问题？ | 版本差异、脚本兼容性、QoR 对比方法 | 01 + 09 + 10 | 工具升级, QoR, 对比 | hard |
| 9 | 跨时钟域的 CDC 问题能在综合阶段发现吗？ | CDC 检查工具、综合约束、静态分析 | 03 + 07 + 09 | CDC, 跨时钟域, 静态分析 | hard |
| 10 | DFT 插入后原来 timing met 的路径变违例了，正常吗？ | DFT 对时序的影响、scan insert 后重综合 | 04 + 07 + 09 | DFT, timing, scan insert | hard |
| 11 | 综合脚本中 `set_dont_touch` 用多了会有什么副作用？ | don't touch 影响优化空间、面积和时序 | 02 + 04 + 05 | dont_touch, 优化, area, timing | medium |
| 12 | 红区和绿区的综合环境配置有什么差异需要注意？ | 区域隔离、数据同步、配置差异 | 11 + 01 | 红区, 绿区, 跨区, 综合环境 | hard |
| 13 | 综合结果和后端 STA 结果差异很大，哪个更可信？ | 综合用 wireload model 估计 vs 后端实际寄生参数 | 01 + 08 + 10 | STA, wireload, 后端, 精度 | hard |
| 14 | 一个模块综合时间特别长（>2小时），怎么优化综合脚本提高效率？ | 脚本优化、compile 策略、层次化综合 | 02 + 04 + 10 | 综合效率, compile, 层次化 | medium |
| 15 | 工具报 "max transition violation" 和 "max capacitance violation" 分别意味着什么？怎么修？ | DRC 约束、驱动能力、buffer 插入 | 03 + 04 + 09 | max_transition, max_capacitance, DRC, buffer | medium |

---

## 五、边界测试（8 题）

> 考察知识库对模糊查询、空结果、超范围问题的处理能力。

| # | 问题 | 预期行为 | 核心检索词 | 难度 |
|---|------|---------|-----------|------|
| 1 | 布局布线怎么做？ | 应回答"超出综合知识库范围"或给出有限信息 | 布局布线, P&R, 后端 | easy |
| 2 | Verilog 语法教程 | 应说明知识库侧重综合而非 RTL 编写 | Verilog, RTL, 语法 | easy |
| 3 | Python 怎么调用 DC？ | 可能部分相关（脚本自动化），但不完全在范围内 | Python, DC, 自动化 | medium |
| 4 | 综合工具 license 不够用怎么办？ | 超出技术范围，应说明 | license, 工具, 管理 | easy |
| 5 | DC 和 Genus 哪个市场占有率高？ | 可能无直接答案，应如实说明 | DC, Genus, 市场份额 | easy |
| 6 | FPGA 综合和 ASIC 综合的区别？ | 应说明知识库侧重 ASIC 综合 | FPGA, ASIC, 综合 | medium |
| 7 | 什么是 STA？它和综合有什么关系？ | 应能回答部分（综合中的 timing analysis） | STA, timing analysis, 静态时序 | medium |
| 8 | 芯片功耗的计算公式是什么？ | 可能有部分答案（动态功耗 = αCV²f） | 功耗公式, 动态功耗, αCV²f | medium |

---

## 附录 A：问题分布统计

### 按语言分类

| 语言类型 | 数量 | 占比 |
|---------|------|------|
| 纯中文 | 39 | 42% |
| 纯英文 | 27 | 29% |
| 中英混合 | 27 | 29% |
| **合计** | **93** | **100%** |

### 按难度分类

| 难度 | 数量 | 占比 |
|------|------|------|
| easy | 33 | 35% |
| medium | 37 | 40% |
| hard | 23 | 25% |

### 按分类统计（核心检索词出现频次）

| 分类 | 作为主要命中 | 作为辅助命中 | 核心检索词出现次数 |
|------|-------------|-------------|-------------------|
| 01-综合基础 | 6 | 12 | DC(15), Genus(12), compile(8), QoR(6), 综合流程(5) |
| 02-TCL脚本 | 5 | 10 | TCL(10), script(8), 命令(7), 模板(4) |
| 03-时序约束 | 10 | 14 | SDC(18), clock(15), input_delay(4), output_delay(4), multicycle(6), false path(7) |
| 04-时序优化 | 8 | 16 | timing(20), setup(8), hold(7), clock gating(14), critical path(4) |
| 05-面积优化 | 4 | 10 | area(16), resource sharing(5), FSM(5), encoding(5) |
| 06-功耗优化 | 7 | 12 | power(16), UPF(14), multi-Vt(7), isolation(7), level shifter(6) |
| 07-DFX | 4 | 8 | DFT(12), scan chain(9), BIST(4), ATPG(4) |
| 08-后端接口 | 4 | 11 | netlist(10), DEF(5), LEF(4), P&R(8), STA(5) |
| 09-常见问题 | 6 | 13 | DRC(12), LVS(6), error(8), fix(7), troubleshoot(3) |
| 10-实战案例 | 3 | 10 | 案例(5), 经验(6), 收敛(4), 优化过程(3) |
| 11-红区绿区 | 2 | 4 | 红区(4), 绿区(4), 跨区(3), 同步(2), 安全(2) |

---

## 附录 B：问题设计原则

### 问题类型说明

1. **精准查询词问题**：包含精确 EDA 术语/命令名，测试精确匹配能力
2. **多文档综合问题**：需综合 3+ 篇不同分类文档，测试 RRF 融合能力
3. **语义近似问题**：同一问题用 2-3 种不同表述，测试语义检索鲁棒性
4. **隐含关联问题**：不含直接分类关键词，答案需跨文档推理
5. **边界测试**：超范围或模糊查询，测试拒答/范围识别能力

### 语言配比设计

- **纯中文**（~40%）：如"时钟门控怎么降低功耗？"、"DRC 报告怎么修？"
- **纯英文**（~30%）：如"How to use set_clock_gating_style?"、"What is a false path?"
- **中英混合**（~30%）：如"DC 中怎么 set_false_path？"、"Genus 的 QoR 报告怎么看？"

### 难度分级标准

- **easy**：问题明确，答案直接，通常命中 1-2 篇文档
- **medium**：需要一定推理，可能命中 2-3 篇文档
- **hard**：需要深入理解或多步推理，通常命中 3+ 篇文档

---

## 附录 C：使用方法

1. 逐题执行 `search(question)` 并记录召回的文档名
2. 对照"预期命中分类"判断召回是否准确
3. 统计每类问题的召回率、精确率
4. 重点关注"多文档综合"和"语义近似"两组的 RRF 融合效果
5. 重点关注"隐含关联"组对隐含语义的捕捉能力
6. 输出评测报告，按分类汇总通过率
7. 对边界测试题，验证拒答行为是否合理
8. 按语言分组统计，确保中文/英文/混合查询的召回率差异在 10% 以内
