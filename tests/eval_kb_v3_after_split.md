# SynHub KB 检索评估报告 v2

生成时间: 2026-08-25 19:54:04
总耗时: 511.0s
问题总数: 53

## 1. 总览

| 指标 | 值 |
|------|-----|
| 通过数 | 47 / 53 |
| **通过率** | **88.7%** |
| 错误数 | 0 |

### 各维度平均分

| 维度 | 平均分 | 满分 |
|------|--------|------|
| 召回率 | 27.2 | 30 |
| 精确率 | 25.5 | 30 |
| RRF 质量 | 12.7 | 20 |
| 语义匹配 | 14.3 | 20 |
| **总分** | **79.7** | **100** |

## 2. 按技术域汇总

| 域 | 名称 | 题数 | 平均召回 | 平均精确 | 平均 RRF | 平均语义 | 域总分 |
|------|------|------|----------|----------|----------|----------|--------|
| A | 时钟与时序约束 | 7 | 30.0 | 24.0 | 12.9 | 13.0 | 79.9 |
| B | 多电源域 CLP 规则 | 7 | 28.6 | 28.3 | 12.6 | 14.6 | 84.0 |
| C | LP cell 物理实现 | 8 | 27.5 | 25.5 | 12.2 | 13.1 | 78.3 |
| D | Memory 综合 | 5 | 30.0 | 28.8 | 12.0 | 16.4 | 87.2 |
| E | RTL 工具链 | 4 | 30.0 | 30.0 | 14.0 | 15.2 | 89.2 |
| G | 流程规范 | 4 | 26.2 | 26.2 | 14.0 | 14.3 | 80.8 |
| semantic | 语义近似 | 3 | 5.7 | 4.0 | 10.2 | 11.0 | 30.9 |
| boundary | 边界/拒答 | 3 | 30.0 | 30.0 | 20.0 | 17.1 | 97.1 |

## 3. 按知识库汇总（辅助视图）

| 知识库 | 题数 | 平均总分 |
|--------|------|----------|
| SDC | 8 | 72.4 |
| Memory | 6 | 79.0 |
| 低功耗 | 4 | 89.2 |

## 4. 每题明细

| id | 域 | 类型 | 问题 | 召回 | 精确 | RRF | 语义 | 总分 | 状态 | 诊断 |
|------|------|------|------|------|------|-----|------|------|------|------|
| A-01 | A | single_doc | SDC 由哪几部分构成? | 30.0 | 30.0 | 12.0 | 11.6 | 83.6 | PASS | — |
| A-02 | A | single_doc | signoff 阶段 SDC group 的设置原则是什么? | 30.0 | 30.0 | 14.0 | 15.0 | 89.0 | PASS | — |
| A-03 | A | single_doc | SDC 架构和模板长什么样? | 30.0 | 10.0 | 12.0 | 13.6 | 65.6 | PASS | — |
| A-04 | A | single_doc | function 相关的约束怎么理解? | 30.0 | 30.0 | 14.0 | 14.6 | 88.6 | PASS | — |
| A-05 | A | single_doc | SDC exception 有哪几类? | 30.0 | 20.0 | 12.0 | 9.2 | 71.2 | PASS | — |
| A-06 | A | multi_doc | STC 用户指南和 STC skew 方法学讲了什么? | 30.0 | 18.0 | 12.0 | 13.3 | 73.3 | PASS | — |
| A-07 | A | single_doc | XMI_ANA* 模拟信号一致性检查怎么做? | 30.0 | 30.0 | 14.0 | 13.9 | 87.9 | PASS | — |
| B-01 | B | single_doc | uncertainty / max_tran / max_cap check 应... | 30.0 | 30.0 | 12.0 | 19.0 | 91.0 | PASS | — |
| B-02 | B | single_doc | PT default report check 里都检查什么? | 30.0 | 30.0 | 14.0 | 10.1 | 84.1 | PASS | — |
| B-03 | B | single_doc | asynchronous / logical exclusive / physi... | 30.0 | 30.0 | 12.0 | 16.7 | 88.7 | PASS | — |
| B-04 | B | single_doc | Timing spec 规范应该怎么写? | 30.0 | 30.0 | 12.0 | 15.6 | 87.6 | PASS | — |
| B-05 | B | single_doc | Hold margin 该怎么 check? | 30.0 | 30.0 | 12.0 | 15.7 | 87.7 | PASS | — |
| B-06 | B | multi_doc | POCV+OCV 场景下,Check derate 和 Common Clock... | 20.0 | 18.0 | 12.0 | 11.1 | 61.1 | PASS | — |
| B-07 | B | single_doc | STA flow 和 gen SDF flow 有什么对比差异? | 30.0 | 30.0 | 14.0 | 13.9 | 87.9 | PASS | — |
| C-01 | C | single_doc | COT SYN / LEC / CLP / PRE_STA 整体 FLOW 是什... | 30.0 | 30.0 | 12.0 | 18.8 | 90.8 | PASS | — |
| C-02 | C | single_doc | Synthesis strategy template 里都包含哪些设置? | 30.0 | 30.0 | 14.0 | 15.0 | 89.0 | PASS | — |
| C-03 | C | single_doc | Genus 出现 congestion 应该怎么排查和优化? | 30.0 | 30.0 | 4.0 | 10.1 | 74.1 | PASS | — |
| C-04 | C | single_doc | Uniquify design 的执行策略有哪些? | 30.0 | 30.0 | 14.0 | 11.7 | 85.7 | PASS | — |
| C-05 | C | single_doc | stdcell 选型该怎么研究? | 30.0 | 30.0 | 16.0 | 16.9 | 92.9 | PASS | — |
| C-06 | C | multi_doc | LEC / conformal 的整体 flow 和 run step 是怎样的... | 10.0 | 6.0 | 12.0 | 6.7 | 34.7 | FAIL | — |
| C-07 | C | single_doc | MMMC(multi-mode multi-corner)方案怎么评估? | 30.0 | 30.0 | 12.0 | 12.6 | 84.6 | PASS | — |
| C-08 | C | multi_doc | Fourier RTL1p0 综合和 Franklin4 综合策略分别是怎么规划... | 30.0 | 18.0 | 14.0 | 12.8 | 74.8 | PASS | — |
| D-01 | D | single_doc | COT syn memory 的整体说明? | 30.0 | 30.0 | 6.0 | 19.0 | 85.0 | PASS | — |
| D-02 | D | single_doc | Memory Wrapper RTL 自动生成的整体思路是什么? | 30.0 | 30.0 | 14.0 | 18.9 | 92.9 | PASS | — |
| D-03 | D | single_doc | 自研 sram verilog model 的后门函数和宏开关有哪些? | 30.0 | 30.0 | 14.0 | 14.1 | 88.1 | PASS | — |
| D-04 | D | single_doc | 后仿 memory 出现 X 态问题怎么排查? | 30.0 | 30.0 | 12.0 | 13.4 | 85.4 | PASS | — |
| D-05 | D | multi_doc | franklin memory gen&wrapper 和 isp_v400 m... | 30.0 | 24.0 | 14.0 | 16.7 | 84.7 | PASS | — |
| E-01 | E | single_doc | Retention register 是什么? | 30.0 | 30.0 | 14.0 | 12.4 | 86.4 | PASS | — |
| E-02 | E | single_doc | VCS 不支持哪些 UPF 格式? | 30.0 | 30.0 | 14.0 | 16.6 | 90.6 | PASS | — |
| E-03 | E | single_doc | Synthesis power 优化策略有哪些? | 30.0 | 30.0 | 14.0 | 16.2 | 90.2 | PASS | — |
| E-04 | E | multi_doc | Fourier BB_MPW 的 low power 实现方案和 v400 UP... | 30.0 | 30.0 | 14.0 | 15.6 | 89.6 | PASS | — |
| F-01 | F | single_doc | DFT MBIST 流程怎么走? | 30.0 | 30.0 | 12.0 | 18.2 | 90.2 | PASS | — |
| F-02 | F | single_doc | ECO 中 scan chain 有什么典型问题? | 30.0 | 30.0 | 12.0 | 19.0 | 91.0 | PASS | — |
| F-03 | F | single_doc | Lauda V010 DFT 面积异常增长的原因怎么排查? | 30.0 | 30.0 | 14.0 | 15.6 | 89.6 | PASS | — |
| G-01 | G | single_doc | Synthesis PPA 的评估目标是什么? | 30.0 | 30.0 | 14.0 | 17.2 | 91.2 | PASS | — |
| G-02 | G | single_doc | Joules netlist 功耗分析的指南? | 30.0 | 30.0 | 14.0 | 17.9 | 91.9 | PASS | — |
| G-03 | G | single_doc | ISP SVT / LVT / ULVT 的比例是多少?怎么选? | 30.0 | 30.0 | 14.0 | 10.9 | 84.9 | PASS | — |
| G-04 | G | multi_doc | Lauda falcon_l2_drt31_wrap 功耗异常和 Joules ... | 15.0 | 15.0 | 14.0 | 11.1 | 55.1 | FAIL | — |
| H-01 | H | single_doc | v400 signoff daily 记录长什么样? | 30.0 | 30.0 | 16.0 | 16.6 | 92.6 | PASS | — |
| H-02 | H | single_doc | Formal 策略及约束怎么设置? | 30.0 | 30.0 | 16.0 | 14.1 | 90.1 | PASS | — |
| H-03 | H | multi_doc | F3 pin2pin 和 F4 pin2pin 综合实现方案有什么差异? | 30.0 | 30.0 | 12.0 | 13.2 | 85.2 | PASS | — |
| I-01 | I | single_doc | 综合流程提效结题报告讲了哪些提效点? | 30.0 | 30.0 | 6.0 | 16.2 | 82.2 | PASS | — |
| I-02 | I | multi_doc | lauda1 falcon_cluster_top 1.0 release 出口... | 30.0 | 24.0 | 12.0 | 17.4 | 83.4 | PASS | — |
| J-01 | J | single_doc | 案例:set_max_delay -through 不能 override 前面... | 30.0 | 30.0 | 4.0 | 10.7 | 74.7 | PASS | — |
| J-02 | J | single_doc | 案例:timing path 在 genus/innovus 里能看到,但在 P... | 0.0 | 0.0 | 4.0 | 8.0 | 12.0 | FAIL | — |
| J-03 | J | single_doc | 案例:ETM 抽出来的时钟频率不对怎么排查? | 30.0 | 30.0 | 12.0 | 12.4 | 84.4 | PASS | — |
| J-04 | J | multi_doc | Debug Genus syn opt crash 和 ispatial flo... | 30.0 | 18.0 | 12.0 | 15.8 | 75.8 | PASS | — |
| S-01 | semantic | semantic_group | What are the components of an SDC file? ... | 3.1 | 0.0 | 6.7 | 10.0 | 19.8 | FAIL | J=0.10 |
| S-02 | semantic | semantic_group | How to fix Genus placement congestion? |... | 6.4 | 6.0 | 12.0 | 10.4 | 34.8 | FAIL | J=0.21 |
| S-03 | semantic | semantic_group | How is memory wrapper RTL auto-generated... | 7.5 | 6.0 | 12.0 | 12.5 | 38.0 | FAIL | J=0.25 |
| X-01 | boundary | boundary | 如何用 Python 训练一个 CNN 图像分类模型? | 30.0 | 30.0 | 20.0 | 18.1 | 98.1 | PASS | s_max=0.09 |
| X-02 | boundary | boundary | 中芯国际 12 寸晶圆代工的报价是多少? | 30.0 | 30.0 | 20.0 | 16.5 | 96.5 | PASS | s_max=0.18 |
| X-03 | boundary | boundary | Verilog testbench 中随机化 sequence 怎么写? | 30.0 | 30.0 | 20.0 | 16.7 | 96.7 | PASS | s_max=0.16 |

## 5. 边界题诊断

| id | 问题 | s_max | noise 命中 | 总分 |
|------|------|-------|------------|------|
| X-01 | 如何用 Python 训练一个 CNN 图像分类模型? | 0.094 | 无 | 98.1 |
| X-02 | 中芯国际 12 寸晶圆代工的报价是多少? | 0.175 | 无 | 96.5 |
| X-03 | Verilog testbench 中随机化 sequence 怎么写? | 0.163 | 无 | 96.7 |

## 7. 失败题详情

### C-06: LEC / conformal 的整体 flow 和 run step 是怎样的?

- 域: C / 子域: 
- 类型: multi_doc / 难度: mid
- 总分: 34.7 / 100
- 召回: 10.0/30, 精确: 6.0/30, RRF: 12.0/20, 语义: 6.7/20
- 预期文档: AkxmdLM3do7H5Pxm5d6cRsNOn1c.md, D2sPdXUlmoGDKWxzTtzc2PLpn1b.md, ULiHdx5z6o0iVcx7OIAcFE88nKh.md
- 命中文档: ULiHdx5z6o0iVcx7OIAcFE88nKh.md

### G-04: Lauda falcon_l2_drt31_wrap 功耗异常和 Joules 功耗结果异常对比的案例分别讲了什么?

- 域: G / 子域: 
- 类型: multi_doc / 难度: hard
- 总分: 55.1 / 100
- 召回: 15.0/30, 精确: 15.0/30, RRF: 14.0/20, 语义: 11.1/20
- 预期文档: MVSMdAr1soHLRHxYHsxcviFqnyf.md, VMiLdK9iIo0cnwx1HkVch63mnRe.md
- 命中文档: MVSMdAr1soHLRHxYHsxcviFqnyf.md

### J-02: 案例:timing path 在 genus/innovus 里能看到,但在 PT 里看不到,原因是什么?

- 域: J / 子域: 
- 类型: single_doc / 难度: mid
- 总分: 12.0 / 100
- 召回: 0.0/30, 精确: 0.0/30, RRF: 4.0/20, 语义: 8.0/20
- 预期文档: CKCwdZaBJoP0KAx7EYLcqFaZnVg.md
- 命中文档: 无

### S-01: What are the components of an SDC file? | 一份 sdc 文件里都写些什么内容? | CF7Wd1JspooMDIxC53fcwLaqnVg.md

- 域: semantic / 子域: 
- 类型: semantic_group / 难度: mid
- 总分: 19.8 / 100
- 召回: 3.1/30, 精确: 0.0/30, RRF: 6.7/20, 语义: 10.0/20
- 命中文档: 无
- Jaccard 均值: 0.104
- 三者交集占比: 0.000

### S-02: How to fix Genus placement congestion? | 综合阶段 congestion 报警怎么调? | RGkcdQbvLokX0oxOhUCcZGYrnIc.md

- 域: semantic / 子域: 
- 类型: semantic_group / 难度: mid
- 总分: 34.8 / 100
- 召回: 6.4/30, 精确: 6.0/30, RRF: 12.0/20, 语义: 10.4/20
- 命中文档: 无
- Jaccard 均值: 0.214
- 三者交集占比: 0.200

### S-03: How is memory wrapper RTL auto-generated? | 存储器 wrapper 自动化生成的整体流程? | PDOJdZbFyoQqyTxXWqscBp0bnbg.md

- 域: semantic / 子域: 
- 类型: semantic_group / 难度: mid
- 总分: 38.0 / 100
- 召回: 7.5/30, 精确: 6.0/30, RRF: 12.0/20, 语义: 12.5/20
- 命中文档: 无
- Jaccard 均值: 0.250
- 三者交集占比: 0.200
