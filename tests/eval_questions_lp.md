# SynHub 低功耗领域知识库评测问题集

针对芯片低功耗设计领域 93 篇文档设计，覆盖 5 类问题：CLP 规则、UPF 实现、LP Cell、流程配置、案例分析。
共 30 道问题。

---

## 一、CLP 规则类（10 题）

> 每题针对具体 CLP error code，要求精确命中对应文档。

| # | 问题 | 预期命中文档 | 核心检索词 | 难度 |
|---|------|-------------|-----------|------|
| 1 | CLP 报 ISO_NO_STRATEGY_OFF_TO_ON_PATH_NOISO 错误，是什么意思？UPF 中应该怎么修？ | 1801_ISO_NO_STRATEGY_OFF_ON_PATH_NOISO | ISO_NO_STRATEGY, OFF_TO_ON_PATH, isolation strategy, UPF, 未插入 | easy |
| 2 | 一个信号被 tie 值为 1，但工具给它插了 clamp 值为 0 的 isolation cell，CLP 报 ISO_CLAMP_VALUE_CONFLICT，怎么理解这个冲突？ | 1801_ISO_CLAMP_VALUE_CONFLICT | clamp_value, conflict, tie, isolation, ISO_CLAMP_VALUE | easy |
| 3 | supply set 没有对应的 power state 时报 SUPPLY_NET_HAS_NO_STATE，该怎么在 UPF 中补充定义 power state？ | 1801_SUPPLY_NET_HAS_NO_STATE | supply_net, power_state, SUPPLY_NET_HAS_NO_STATE, supply set, 定义 | medium |
| 4 | CLP 报 SUPPLY_STATE_TOOL_DERIVED，工具自动推导了 power state，为什么这不是好事？ | 1801_SUPPLY_STATE_TOOL_DERIVED | TOOL_DERIVED, power state, supply state, UPF 定义, 自动推导 | medium |
| 5 | CLP 报 REF_OBJ_NOT_FOUND 找不到引用对象，常见原因有哪些？怎么定位？ | 1801_REF_OBJ_NOT_FOUND | REF_OBJ_NOT_FOUND, reference object, 引用对象, 未找到, 定位 | easy |
| 6 | 从 off 域到 on 域的信号 crossing 没有插 level shifter，CLP 报 CROSSING_OFF_TO_ON_LSH，怎么修？ | CROSSING_OFF_TO_ON_LSH | OFF_TO_ON_LSH, level shifter, crossing, 电压域, off to on | medium |
| 7 | CROSSING_OFF_TO_ON_AON 和 CROSSING_OFF_TO_ON_LSH 有什么区别？AON 相关的 crossing 检查关注什么？ | CROSSING_OFF_TO_ON_AON | OFF_TO_ON_AON, always-on, crossing, AON, 区别 | medium |
| 8 | CLP 报 ISO_REDUNDANT 和 ISO_ELS_REDUNDANT，冗余 isolation cell 的判断标准是什么？ | ISO_REDUNDANT / ISO_ELS_REDUNDANT | ISO_REDUNDANT, ELS_REDUNDANT, isolation, 冗余, 判断标准 | medium |
| 9 | LSH_REDUNDANT 和 LSH_ELS_REDUNDANT 报错时，什么情况下 level shifter 会被判定为冗余？ | LSH_REDUNDANT / LSH_ELS_REDUNDANT | LSH_REDUNDANT, level shifter, 冗余, ELS, 判定 | medium |
| 10 | CLP 报 PG_CONN_SUPPLY_PIN_CONN_MISSING 或 PG_CONN_SUPPLY_PIN_UNDRIVEN 或 PG_CONN_SUPPLY_PORT_UNDEFINED，电源连接问题怎么排查？ | PG_CONN_SUPPLY_PIN_CONN_MISSING / PG_CONN_SUPPLY_PIN_UNDRIVEN / PG_CONN_SUPPLY_PORT_UNDEFINED | PG_CONN, supply_pin, UNDRIVEN, PORT_UNDEFINED, 电源连接 | hard |

---

## 二、UPF 实现类（8 题）

> 针对 UPF flow、power switch 配置、power domain 管理等内容。

| # | 问题 | 预期命中文档 | 核心检索词 | 难度 |
|---|------|-------------|-----------|------|
| 11 | UPF gen flow 中 power switch 的参数配置包含哪些？ack_delay、ack1、ack2、control1、control2 分别怎么设置？ | UPF gen flow | power_switch, ack_delay, ack1, ack2, control1, control2, input_supply, output_supply | medium |
| 12 | UPF 实现中 low power cell 为什么不能集中放在 channel 中？空的 pwr_wrap 为什么不要单独作为一个电源域？ | upf实现需注意的事项 | low power cell, channel, pwr_wrap, 电源域, 注意事项, 集中放置 | medium |
| 13 | Genus 工具报 CPI-100 warning 导致 isolation 插不进去，这个案例的根本原因和解决方法是什么？ | 案例：【UPF】genus报CPI-100 warning，插不进ISO的案例 | CPI-100, Genus, isolation, 插入失败, warning, 根因 | hard |
| 14 | ISO 插入位置不符合预期但通过了 CLP rule check，这种情况下需要关注什么？ | 案例：【UPF】ISO插入位置不符合预期但符合clp rule check的一种情况 | ISO 插入位置, CLP rule check, isolation, 预期, 符合规则 | hard |
| 15 | 前仿报 PSW 的 ack 信号 multidriven error，这个问题的原因是什么？UPF 中应该怎么处理？ | 案例：【UPF/CLP】前仿报PSW的ack信号multidriven error | PSW, ack, multidriven, power switch, 前仿, error | hard |
| 16 | STRATEGY_SUPPLY_SET_CONFLICT_AON 和 STRATEGY_SUPPLY_SET_CONFLICT_LSH 报错分别表示什么？supply set 冲突怎么解决？ | STRATEGY_SUPPLY_SET_CONFLICT_AON / LSH | supply_set, conflict, AON, LSH, strategy, supply set 冲突 | hard |
| 17 | SUPPLY_SET_DOMAIN_CONFLICT 报错是什么意思？supply set 和 power domain 冲突怎么排查？ | SUPPLY_SET_DOMAIN_CONFLICT | supply_set, domain, conflict, SUPPLY_SET_DOMAIN_CONFLICT, 冲突 | medium |
| 18 | ISO_DATA_CONST_CLAMP_VALUE_CONFLICT 报错是什么意思？数据常量和 clamp 值冲突怎么解决？ | ISO_DATA_CONST_CLAMP_VALUE_CONFLICT | data_const, clamp_value, conflict, ISO, 数据常量 | medium |

---

## 三、LP Cell 类（5 题）

> 针对 isolation cell、level shifter、MTCMOS、power switch 等低功耗单元的使用规则。

| # | 问题 | 预期命中文档 | 核心检索词 | 难度 |
|---|------|-------------|-----------|------|
| 19 | Lowpower cell 级联情况下，多个 LP cell 串在一起时有什么规则和限制？ | Lowpower cell 级联情况 | LP cell, 级联, 级联规则, low power boundary, 串连 | medium |
| 20 | Low power cell 反向检查的流程是什么？从 low power boundary 反向检查能发现什么问题？ | Low power cell 反向检查 | 反向检查, low power boundary, LP cell, 检查流程, 发现问题 | medium |
| 21 | CLP PNR check 中 MTCMOS chain 检查关注什么？MTCMOS 串链会带来什么风险？ | clp_pnr check MTCMOS chain | MTCMOS, chain, 串链, clp_pnr, 检查, 风险 | medium |
| 22 | Power Switch 的控制端口和 ack 端口带/不带 hier 层级时，CLP RTL 检查和 LEC 结果有什么差异？ | PSW 的描述 / PSW control port和ack port带/不带hier层级clp rtl以及LEC结果对比分析 | PSW, control port, ack port, hier, LEC, CLP RTL | hard |
| 23 | Isolation cell 的测试实现方案是什么？怎么验证 ISO cell 在流片后的功能正确性？ | iso cell测试实现方案 | iso cell, 测试, 测试方案, isolation, 验证, 流片 | medium |

---

## 四、流程与配置类（4 题）

> 针对低功耗综合配置、CLP waive 规范、SOP 流程等内容。

| # | 问题 | 预期命中文档 | 核心检索词 | 难度 |
|---|------|-------------|-----------|------|
| 24 | 低功耗综合的 YAML 配置格式中 low_power_config 字段的 type、module、in、out、src、dest 分别代表什么？ | 低功耗综合相关配置说明 | YAML, low_power_config, type, module, src, dest, 配置格式 | medium |
| 25 | CLP waive 的规范化流程是什么？waive list 和 waive 脚本怎么配合使用？ | Clp waive规范（waive list和脚本介绍） | CLP waive, waive list, waive 脚本, 规范化, 流程 | medium |
| 26 | CLP 报告中 isolation enable 信号的 driver 掉电但 input pin 有电，这种问题怎么分析和修复？ | clp报告分析 | CLP 报告, isolation enable, driver 掉电, input pin, 分析, 修复 | medium |
| 27 | COT-SYN 低功耗实现 SOP 中，从 RTL 到 CLP signoff 的完整流程包含哪些关键步骤？ | COT-SYN 低功耗实现 SOP建设 | SOP, 低功耗实现, CLP signoff, 流程, 步骤, RTL | hard |

---

## 五、案例分析类（3 题）

> 基于实际低功耗项目案例的问题，需要结合案例内容进行分析。

| # | 问题 | 预期命中文档 | 核心检索词 | 难度 |
|---|------|-------------|-----------|------|
| 28 | rst_phyacc_aon_n 的 wrap cell 插入导致了环回问题，这个问题是怎么产生的？根因是什么？ | 案例：【SYN】rst_phyacc_aon_n wrap cell 插入导致环回问题 | rst_phyacc_aon_n, wrap cell, 环回问题, 插入, 根因 | hard |
| 29 | CLP 未发现 NPU mesh LVL 类型错误，这个案例复盘中总结了哪些 CLP 检查的盲区和改进措施？ | 【案例复盘】CLP未发现npu mesh lvl类型错误 | CLP, NPU mesh, LVL 类型错误, 案例复盘, 盲区, 改进 | hard |
| 30 | Phyacc rst_phyacc_aon_n 在 UPF 中需要单独指定双阱 buffer 来定义 LS Rule 并插入 Level Shifter，为什么要这么做？ | Phyacc rst_phyacc_aon_n 处理 | rst_phyacc_aon_n, 双阱 buffer, LS Rule, Level Shifter, UPF, 双阱 | hard |

---

## 附录：问题分布统计

### 按类型分类

| 类型 | 题数 | 占比 |
|------|------|------|
| CLP 规则类 | 10 | 33.3% |
| UPF 实现类 | 8 | 26.7% |
| LP Cell 类 | 5 | 16.7% |
| 流程与配置类 | 4 | 13.3% |
| 案例分析类 | 3 | 10.0% |
| **合计** | **30** | **100%** |

### 按难度分类

| 难度 | 题数 | 占比 |
|------|------|------|
| easy | 4 | 13.3% |
| medium | 14 | 46.7% |
| hard | 12 | 40.0% |
| **合计** | **30** | **100%** |

### 核心检索词覆盖统计

| 检索词类别 | 覆盖的题号 | 出现次数 |
|-----------|-----------|---------|
| CLP error code (如 1801_ISO_*, CROSSING_*, PG_CONN_*) | 1-10 | 10 |
| UPF/power switch/电源域 | 11-18 | 8 |
| LP cell (isolation/level shifter/MTCMOS/PSW) | 19-23 | 5 |
| 流程配置 (YAML/waive/SOP/CLP报告) | 24-27 | 4 |
| 案例关键词 (rst_phyacc/NPU/环回/ack) | 28-30 | 3 |

### 检索命中策略

- **单文档精准命中**：题 1-9, 11-14, 19-26 各应命中 1-2 篇文档
- **需要综合多篇文档**：题 10, 15-18, 22, 27 应命中 2-3 篇文档
- **深度案例分析**：题 28-30 需要精准命中案例文档并理解上下文

---

## 使用方法

1. 逐题执行 `search(question)` 并记录召回的文档名
2. 对照"预期命中文档"判断召回是否准确
3. 特别关注 CLP error code 类问题（题 1-10）的精确命中率
4. 统计各类型问题的召回率和精确率
5. 输出评测报告，按类型汇总通过率
