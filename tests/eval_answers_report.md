# SynHub 低功耗知识库答案质量评测报告

生成时间: 2026-05-18 22:04:36
总耗时: 142.1s
问题总数: 30

## 1. 总览

| 指标 | 值 |
|------|-----|
| 总题数 | 30 |
| 通过题数 (>=60分) | 15 |
| **通过率** | **50.0%** |
| 标杆题数 (>=90分) | 1 |
| 错误题数 | 0 |

## 2. 按类型统计

| 题目类型 | 总数 | 通过数 | 通过率 | 平均分 |
|----------|------|--------|--------|--------|
| CLP 规则类 | 10 | 4 | 40.0% | 51.3 |
| UPF 实现类 | 8 | 4 | 50.0% | 57.6 |
| LP Cell 类 | 5 | 2 | 40.0% | 59.6 |
| 流程与配置类 | 4 | 2 | 50.0% | 59.8 |
| 案例分析类 | 3 | 3 | 100.0% | 71.0 |

### 各维度平均分

| 维度 | 平均分 | 满分 |
|------|--------|------|
| 召回率 | 15.2 | 30 |
| 精确率 | 13.6 | 30 |
| 检索分数 | 16.7 | 20 |
| 内容相关性 | 12.0 | 20 |
| **总分** | **57.5** | **100** |

## 3. 每题详情

| 编号 | 题目类型 | 问题 | 召回 | 精确 | 检索分 | 内容分 | 总分 | 状态 |
|------|----------|------|------|------|--------|--------|------|------|
| 1 | CLP 规则类 | CLP 报 ISO_NO_STRATEGY_OFF_TO_O... | 15.0 | 10.0 | 15.0 | 4.0 | 44.0 | FAIL |
| 2 | CLP 规则类 | 一个信号被 tie 值为 1，但工具给它插了 clamp 值... | 15.0 | 11.5 | 20.0 | 20.0 | 66.5 | PASS |
| 3 | CLP 规则类 | supply set 没有对应的 power state 时... | 15.0 | 11.5 | 20.0 | 4.0 | 50.5 | FAIL |
| 4 | CLP 规则类 | CLP 报 SUPPLY_STATE_TOOL_DERIVE... | 15.0 | 10.0 | 10.0 | 8.0 | 43.0 | FAIL |
| 5 | CLP 规则类 | CLP 报 REF_OBJ_NOT_FOUND 找不到引用对... | 15.0 | 10.0 | 15.0 | 8.0 | 48.0 | FAIL |
| 6 | CLP 规则类 | 从 off 域到 on 域的信号 crossing 没有插 ... | 15.0 | 20.0 | 20.0 | 12.0 | 67.0 | PASS |
| 7 | CLP 规则类 | CROSSING_OFF_TO_ON_AON 和 CROSS... | 0.0 | 0.0 | 15.0 | 12.0 | 27.0 | FAIL |
| 8 | CLP 规则类 | CLP 报 ISO_REDUNDANT 和 ISO_ELS_... | 25.0 | 20.0 | 15.0 | 8.0 | 68.0 | PASS |
| 9 | CLP 规则类 | LSH_REDUNDANT 和 LSH_ELS_REDUND... | 0.0 | 0.0 | 10.0 | 8.0 | 18.0 | FAIL |
| 10 | CLP 规则类 | CLP 报 PG_CONN_SUPPLY_PIN_CONN_... | 25.0 | 20.0 | 20.0 | 16.0 | 81.0 | PASS |
| 11 | UPF 实现类 | UPF gen flow 中 power switch 的参... | 0.0 | 0.0 | 10.0 | 4.0 | 14.0 | FAIL |
| 12 | UPF 实现类 | UPF 实现中 low power cell 为什么不能集中... | 15.0 | 18.5 | 20.0 | 12.0 | 65.5 | PASS |
| 13 | UPF 实现类 | Genus 工具报 CPI-100 warning 导致 i... | 25.0 | 11.5 | 20.0 | 16.0 | 72.5 | PASS |
| 14 | UPF 实现类 | ISO 插入位置不符合预期但通过了 CLP rule che... | 15.0 | 10.0 | 15.0 | 12.0 | 52.0 | FAIL |
| 15 | UPF 实现类 | 前仿报 PSW 的 ack 信号 multidriven e... | 25.0 | 10.0 | 20.0 | 20.0 | 75.0 | PASS |
| 16 | UPF 实现类 | STRATEGY_SUPPLY_SET_CONFLICT_A... | 15.0 | 11.5 | 20.0 | 20.0 | 66.5 | PASS |
| 17 | UPF 实现类 | SUPPLY_SET_DOMAIN_CONFLICT 报错是... | 15.0 | 11.5 | 15.0 | 16.0 | 57.5 | FAIL |
| 18 | UPF 实现类 | ISO_DATA_CONST_CLAMP_VALUE_CON... | 15.0 | 11.5 | 15.0 | 16.0 | 57.5 | FAIL |
| 19 | LP Cell  | Lowpower cell 级联情况下，多个 LP cell... | 15.0 | 11.5 | 15.0 | 4.0 | 45.5 | FAIL |
| 20 | LP Cell  | Low power cell 反向检查的流程是什么？从 lo... | 15.0 | 11.5 | 15.0 | 4.0 | 45.5 | FAIL |
| 21 | LP Cell  | CLP PNR check 中 MTCMOS chain 检... | 15.0 | 23.0 | 20.0 | 12.0 | 70.0 | PASS |
| 22 | LP Cell  | Power Switch 的控制端口和 ack 端口带/不带... | 25.0 | 30.0 | 15.0 | 20.0 | 90.0 | BENCHMARK |
| 23 | LP Cell  | Isolation cell 的测试实现方案是什么？怎么验证... | 15.0 | 10.0 | 10.0 | 12.0 | 47.0 | FAIL |
| 24 | 流程与配置类 | 低功耗综合的 YAML 配置格式中 low_power_co... | 15.0 | 18.5 | 15.0 | 20.0 | 68.5 | PASS |
| 25 | 流程与配置类 | CLP waive 的规范化流程是什么？waive list... | 15.0 | 11.5 | 20.0 | 8.0 | 54.5 | FAIL |
| 26 | 流程与配置类 | CLP 报告中 isolation enable 信号的 d... | 15.0 | 30.0 | 15.0 | 4.0 | 64.0 | PASS |
| 27 | 流程与配置类 | COT-SYN 低功耗实现 SOP 中，从 RTL 到 CL... | 15.0 | 9.2 | 20.0 | 8.0 | 52.2 | FAIL |
| 28 | 案例分析类 | rst_phyacc_aon_n 的 wrap cell 插... | 15.0 | 23.0 | 20.0 | 16.0 | 74.0 | PASS |
| 29 | 案例分析类 | CLP 未发现 NPU mesh LVL 类型错误，这个案例... | 15.0 | 10.0 | 20.0 | 16.0 | 61.0 | PASS |
| 30 | 案例分析类 | Phyacc rst_phyacc_aon_n 在 UPF ... | 15.0 | 23.0 | 20.0 | 20.0 | 78.0 | PASS |

### 命中文档详情

**1.** CLP 报 ISO_NO_STRATEGY_OFF_TO_ON_PATH_NOISO 错误，是什么意...
- 预期文档: 1801_ISO_NO_STRATEGY_OFF_ON_PATH_NOISO
- 命中文档: 1801_ISO_NO_STRATEGY_OFF_ON_PATH_NOISO

**2.** 一个信号被 tie 值为 1，但工具给它插了 clamp 值为 0 的 isolation cell...
- 预期文档: 1801_ISO_CLAMP_VALUE_CONFLICT
- 命中文档: 1801_ISO_CLAMP_VALUE_CONFLICT

**3.** supply set 没有对应的 power state 时报 SUPPLY_NET_HAS_NO_...
- 预期文档: 1801_SUPPLY_NET_HAS_NO_STATE
- 命中文档: 1801_SUPPLY_NET_HAS_NO_STATE

**4.** CLP 报 SUPPLY_STATE_TOOL_DERIVED，工具自动推导了 power stat...
- 预期文档: 1801_SUPPLY_STATE_TOOL_DERIVED
- 命中文档: 1801_SUPPLY_STATE_TOOL_DERIVED

**5.** CLP 报 REF_OBJ_NOT_FOUND 找不到引用对象，常见原因有哪些？怎么定位？...
- 预期文档: 1801_REF_OBJ_NOT_FOUND
- 命中文档: 1801_REF_OBJ_NOT_FOUND

**6.** 从 off 域到 on 域的信号 crossing 没有插 level shifter，CLP 报 ...
- 预期文档: CROSSING_OFF_TO_ON_LSH
- 命中文档: CROSSING_OFF_TO_ON_LSH

**7.** CROSSING_OFF_TO_ON_AON 和 CROSSING_OFF_TO_ON_LSH 有什...
- 预期文档: CROSSING_OFF_TO_ON_AON
- 命中文档: 无

**8.** CLP 报 ISO_REDUNDANT 和 ISO_ELS_REDUNDANT，冗余 isolati...
- 预期文档: ISO_REDUNDANT, ISO_ELS_REDUNDANT
- 命中文档: ISO_REDUNDANT, ISO_ELS_REDUNDANT

**9.** LSH_REDUNDANT 和 LSH_ELS_REDUNDANT 报错时，什么情况下 level ...
- 预期文档: LSH_REDUNDANT, LSH_ELS_REDUNDANT
- 命中文档: 无

**10.** CLP 报 PG_CONN_SUPPLY_PIN_CONN_MISSING 或 PG_CONN_SU...
- 预期文档: PG_CONN_SUPPLY_PIN_CONN_MISSING, PG_CONN_SUPPLY_PIN_UNDRIVEN, PG_CONN_SUPPLY_PORT_UNDEFINED
- 命中文档: PG_CONN_SUPPLY_PIN_CONN_MISSING, PG_CONN_SUPPLY_PIN_UNDRIVEN

**11.** UPF gen flow 中 power switch 的参数配置包含哪些？ack_delay、ac...
- 预期文档: UPF gen flow
- 命中文档: 无

**12.** UPF 实现中 low power cell 为什么不能集中放在 channel 中？空的 pwr_...
- 预期文档: upf实现需注意的事项
- 命中文档: upf实现需注意的事项

**13.** Genus 工具报 CPI-100 warning 导致 isolation 插不进去，这个案例的根...
- 预期文档: 案例：【UPF】genus报CPI-100 warning, 插不进ISO的案例
- 命中文档: 案例：【UPF】genus报CPI-100 warning, 插不进ISO的案例

**14.** ISO 插入位置不符合预期但通过了 CLP rule check，这种情况下需要关注什么？...
- 预期文档: 案例：【UPF】ISO插入位置不符合预期但符合clp rule check的一种情况
- 命中文档: 案例：【UPF】ISO插入位置不符合预期但符合clp rule check的一种情况

**15.** 前仿报 PSW 的 ack 信号 multidriven error，这个问题的原因是什么？UPF ...
- 预期文档: 案例：【UPF, CLP】前仿报PSW的ack信号multidriven error
- 命中文档: 案例：【UPF, CLP】前仿报PSW的ack信号multidriven error

**16.** STRATEGY_SUPPLY_SET_CONFLICT_AON 和 STRATEGY_SUPPLY...
- 预期文档: STRATEGY_SUPPLY_SET_CONFLICT_AON, LSH
- 命中文档: STRATEGY_SUPPLY_SET_CONFLICT_AON

**17.** SUPPLY_SET_DOMAIN_CONFLICT 报错是什么意思？supply set 和 po...
- 预期文档: SUPPLY_SET_DOMAIN_CONFLICT
- 命中文档: SUPPLY_SET_DOMAIN_CONFLICT

**18.** ISO_DATA_CONST_CLAMP_VALUE_CONFLICT 报错是什么意思？数据常量和 ...
- 预期文档: ISO_DATA_CONST_CLAMP_VALUE_CONFLICT
- 命中文档: ISO_DATA_CONST_CLAMP_VALUE_CONFLICT

**19.** Lowpower cell 级联情况下，多个 LP cell 串在一起时有什么规则和限制？...
- 预期文档: Lowpower cell 级联情况
- 命中文档: Lowpower cell 级联情况

**20.** Low power cell 反向检查的流程是什么？从 low power boundary 反向检...
- 预期文档: Low power cell 反向检查
- 命中文档: Low power cell 反向检查

**21.** CLP PNR check 中 MTCMOS chain 检查关注什么？MTCMOS 串链会带来什么...
- 预期文档: clp_pnr check MTCMOS chain
- 命中文档: clp_pnr check MTCMOS chain

**22.** Power Switch 的控制端口和 ack 端口带/不带 hier 层级时，CLP RTL 检查...
- 预期文档: PSW 的描述, PSW control port和ack port带, 不带hier层级clp rtl以及LEC结果对比分析
- 命中文档: PSW control port和ack port带, 不带hier层级clp rtl以及LEC结果对比分析

**23.** Isolation cell 的测试实现方案是什么？怎么验证 ISO cell 在流片后的功能正确性...
- 预期文档: iso cell测试实现方案
- 命中文档: iso cell测试实现方案

**24.** 低功耗综合的 YAML 配置格式中 low_power_config 字段的 type、module...
- 预期文档: 低功耗综合相关配置说明
- 命中文档: 低功耗综合相关配置说明

**25.** CLP waive 的规范化流程是什么？waive list 和 waive 脚本怎么配合使用？...
- 预期文档: Clp waive规范（waive list和脚本介绍）
- 命中文档: Clp waive规范（waive list和脚本介绍）

**26.** CLP 报告中 isolation enable 信号的 driver 掉电但 input pin ...
- 预期文档: clp报告分析
- 命中文档: clp报告分析

**27.** COT-SYN 低功耗实现 SOP 中，从 RTL 到 CLP signoff 的完整流程包含哪些关...
- 预期文档: COT-SYN 低功耗实现 SOP建设
- 命中文档: COT-SYN 低功耗实现 SOP建设

**28.** rst_phyacc_aon_n 的 wrap cell 插入导致了环回问题，这个问题是怎么产生的？...
- 预期文档: 案例：【SYN】rst_phyacc_aon_n wrap cell 插入导致环回问题
- 命中文档: 案例：【SYN】rst_phyacc_aon_n wrap cell 插入导致环回问题

**29.** CLP 未发现 NPU mesh LVL 类型错误，这个案例复盘中总结了哪些 CLP 检查的盲区和改...
- 预期文档: 【案例复盘】CLP未发现npu mesh lvl类型错误
- 命中文档: 【案例复盘】CLP未发现npu mesh lvl类型错误

**30.** Phyacc rst_phyacc_aon_n 在 UPF 中需要单独指定双阱 buffer 来定义...
- 预期文档: Phyacc rst_phyacc_aon_n 处理
- 命中文档: Phyacc rst_phyacc_aon_n 处理

## 4. 问题清单（得分 <60）

共 15 题未通过：

### **[未通过] 1. CLP 报 ISO_NO_STRATEGY_OFF_TO_ON_PATH_NOISO 错误，是什么意思？UPF 中应该怎么修？**

- **总分: 44.0/100** (通过线: 60)
- 题目类型: CLP 规则类
- **失分原因:**
  - 召回率不足 (15.0/30): 仅部分命中预期文档
  - 精确率低 (10.0/30): 检索结果中预期文档占比不足
  - 内容相关性低 (4.0/20): 检索结果未充分包含核心检索词

  - 预期文档: 1801_ISO_NO_STRATEGY_OFF_ON_PATH_NOISO
  - 命中文档: 1801_ISO_NO_STRATEGY_OFF_ON_PATH_NOISO

### **[未通过] 3. supply set 没有对应的 power state 时报 SUPPLY_NET_HAS_NO_STATE，该怎么在 UPF 中补充定义 power state？**

- **总分: 50.5/100** (通过线: 60)
- 题目类型: CLP 规则类
- **失分原因:**
  - 召回率不足 (15.0/30): 仅部分命中预期文档
  - 精确率低 (11.5/30): 检索结果中预期文档占比不足
  - 内容相关性低 (4.0/20): 检索结果未充分包含核心检索词

  - 预期文档: 1801_SUPPLY_NET_HAS_NO_STATE
  - 命中文档: 1801_SUPPLY_NET_HAS_NO_STATE

### **[未通过] 4. CLP 报 SUPPLY_STATE_TOOL_DERIVED，工具自动推导了 power state，为什么这不是好事？**

- **总分: 43.0/100** (通过线: 60)
- 题目类型: CLP 规则类
- **失分原因:**
  - 召回率不足 (15.0/30): 仅部分命中预期文档
  - 精确率低 (10.0/30): 检索结果中预期文档占比不足

  - 预期文档: 1801_SUPPLY_STATE_TOOL_DERIVED
  - 命中文档: 1801_SUPPLY_STATE_TOOL_DERIVED

### **[未通过] 5. CLP 报 REF_OBJ_NOT_FOUND 找不到引用对象，常见原因有哪些？怎么定位？**

- **总分: 48.0/100** (通过线: 60)
- 题目类型: CLP 规则类
- **失分原因:**
  - 召回率不足 (15.0/30): 仅部分命中预期文档
  - 精确率低 (10.0/30): 检索结果中预期文档占比不足

  - 预期文档: 1801_REF_OBJ_NOT_FOUND
  - 命中文档: 1801_REF_OBJ_NOT_FOUND

### **[未通过] 7. CROSSING_OFF_TO_ON_AON 和 CROSSING_OFF_TO_ON_LSH 有什么区别？AON 相关的 crossing 检查关注什么？**

- **总分: 27.0/100** (通过线: 60)
- 题目类型: CLP 规则类
- **失分原因:**
  - 召回率低 (0.0/30): 未能命中预期文档
  - 精确率低 (0.0/30): 检索结果中预期文档占比不足

  - 预期文档: CROSSING_OFF_TO_ON_AON
  - 命中文档: 无

### **[未通过] 9. LSH_REDUNDANT 和 LSH_ELS_REDUNDANT 报错时，什么情况下 level shifter 会被判定为冗余？**

- **总分: 18.0/100** (通过线: 60)
- 题目类型: CLP 规则类
- **失分原因:**
  - 召回率低 (0.0/30): 未能命中预期文档
  - 精确率低 (0.0/30): 检索结果中预期文档占比不足

  - 预期文档: LSH_REDUNDANT, LSH_ELS_REDUNDANT
  - 命中文档: 无

### **[未通过] 11. UPF gen flow 中 power switch 的参数配置包含哪些？ack_delay、ack1、ack2、control1、control2 分别怎么设置？**

- **总分: 14.0/100** (通过线: 60)
- 题目类型: UPF 实现类
- **失分原因:**
  - 召回率低 (0.0/30): 未能命中预期文档
  - 精确率低 (0.0/30): 检索结果中预期文档占比不足
  - 内容相关性低 (4.0/20): 检索结果未充分包含核心检索词

  - 预期文档: UPF gen flow
  - 命中文档: 无

### **[未通过] 14. ISO 插入位置不符合预期但通过了 CLP rule check，这种情况下需要关注什么？**

- **总分: 52.0/100** (通过线: 60)
- 题目类型: UPF 实现类
- **失分原因:**
  - 召回率不足 (15.0/30): 仅部分命中预期文档
  - 精确率低 (10.0/30): 检索结果中预期文档占比不足

  - 预期文档: 案例：【UPF】ISO插入位置不符合预期但符合clp rule check的一种情况
  - 命中文档: 案例：【UPF】ISO插入位置不符合预期但符合clp rule check的一种情况

### **[未通过] 17. SUPPLY_SET_DOMAIN_CONFLICT 报错是什么意思？supply set 和 power domain 冲突怎么排查？**

- **总分: 57.5/100** (通过线: 60)
- 题目类型: UPF 实现类
- **失分原因:**
  - 召回率不足 (15.0/30): 仅部分命中预期文档
  - 精确率低 (11.5/30): 检索结果中预期文档占比不足

  - 预期文档: SUPPLY_SET_DOMAIN_CONFLICT
  - 命中文档: SUPPLY_SET_DOMAIN_CONFLICT

### **[未通过] 18. ISO_DATA_CONST_CLAMP_VALUE_CONFLICT 报错是什么意思？数据常量和 clamp 值冲突怎么解决？**

- **总分: 57.5/100** (通过线: 60)
- 题目类型: UPF 实现类
- **失分原因:**
  - 召回率不足 (15.0/30): 仅部分命中预期文档
  - 精确率低 (11.5/30): 检索结果中预期文档占比不足

  - 预期文档: ISO_DATA_CONST_CLAMP_VALUE_CONFLICT
  - 命中文档: ISO_DATA_CONST_CLAMP_VALUE_CONFLICT

### **[未通过] 19. Lowpower cell 级联情况下，多个 LP cell 串在一起时有什么规则和限制？**

- **总分: 45.5/100** (通过线: 60)
- 题目类型: LP Cell 类
- **失分原因:**
  - 召回率不足 (15.0/30): 仅部分命中预期文档
  - 精确率低 (11.5/30): 检索结果中预期文档占比不足
  - 内容相关性低 (4.0/20): 检索结果未充分包含核心检索词

  - 预期文档: Lowpower cell 级联情况
  - 命中文档: Lowpower cell 级联情况

### **[未通过] 20. Low power cell 反向检查的流程是什么？从 low power boundary 反向检查能发现什么问题？**

- **总分: 45.5/100** (通过线: 60)
- 题目类型: LP Cell 类
- **失分原因:**
  - 召回率不足 (15.0/30): 仅部分命中预期文档
  - 精确率低 (11.5/30): 检索结果中预期文档占比不足
  - 内容相关性低 (4.0/20): 检索结果未充分包含核心检索词

  - 预期文档: Low power cell 反向检查
  - 命中文档: Low power cell 反向检查

### **[未通过] 23. Isolation cell 的测试实现方案是什么？怎么验证 ISO cell 在流片后的功能正确性？**

- **总分: 47.0/100** (通过线: 60)
- 题目类型: LP Cell 类
- **失分原因:**
  - 召回率不足 (15.0/30): 仅部分命中预期文档
  - 精确率低 (10.0/30): 检索结果中预期文档占比不足

  - 预期文档: iso cell测试实现方案
  - 命中文档: iso cell测试实现方案

### **[未通过] 25. CLP waive 的规范化流程是什么？waive list 和 waive 脚本怎么配合使用？**

- **总分: 54.5/100** (通过线: 60)
- 题目类型: 流程与配置类
- **失分原因:**
  - 召回率不足 (15.0/30): 仅部分命中预期文档
  - 精确率低 (11.5/30): 检索结果中预期文档占比不足

  - 预期文档: Clp waive规范（waive list和脚本介绍）
  - 命中文档: Clp waive规范（waive list和脚本介绍）

### **[未通过] 27. COT-SYN 低功耗实现 SOP 中，从 RTL 到 CLP signoff 的完整流程包含哪些关键步骤？**

- **总分: 52.2/100** (通过线: 60)
- 题目类型: 流程与配置类
- **失分原因:**
  - 召回率不足 (15.0/30): 仅部分命中预期文档
  - 精确率低 (9.2/30): 检索结果中预期文档占比不足

  - 预期文档: COT-SYN 低功耗实现 SOP建设
  - 命中文档: COT-SYN 低功耗实现 SOP建设

## 5. 高分标杆题（>=90分）

共 1 道标杆题目：

### **[标杆] 22. Power Switch 的控制端口和 ack 端口带/不带 hier 层级时，CLP RTL 检查和 LEC 结果有什么差异？**
- 总分: **90.0/100**
- 召回率: 25.0/30, 精确率: 30.0/30, 检索分数: 15.0/20, 内容相关性: 20.0/20
- 命中文档: PSW control port和ack port带, 不带hier层级clp rtl以及LEC结果对比分析
