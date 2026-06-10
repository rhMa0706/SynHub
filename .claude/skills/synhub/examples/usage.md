# 使用示例

接入完成后,直接用自然语言提问,Claude 会自动调 `search_synthesis_knowledge` 并按规范回答。

## 场景 1:错误码排查

**用户**:
> CLP error CROSSING_OFF_TO_ON_AON 这个怎么修?

**Claude 行为**:
- 调 `search_synthesis_knowledge(query="CROSSING_OFF_TO_ON_AON CLP")`
- 自动路由到低功耗库
- 错误码桥接:在文档标题里找含 `CROSSING_OFF_TO_ON_AON` 的文档
- 返回相关片段,Claude 给修复方案 + `[文档名]` 来源 + 置信度

## 场景 2:流程查询

**用户**:
> UPF power domain 创建步骤是什么?

**Claude 行为**:
- 调 `search_synthesis_knowledge(query="UPF power domain creation")`
- 自动路由到低功耗库
- 中英桥接:`电源域` → `power domain`
- 返回流程文档片段

## 场景 3:跨域问题(自动并搜)

**用户**:
> Mick 工具里 clp check 怎么做?

**Claude 行为**:
- 关键词 `mick`(memory 库) + `clp`(低功耗库)同时命中 → 两个库一起搜
- RRF 融合后返回综合结果

## 场景 4:列出文档

**用户**:
> 知识库里有哪些 SDC 相关文档?

**Claude 行为**:
- 调 `list_knowledge_categories(dataset_id="b26e181e-fc6c-4371-8a11-3e19580afd85")`
- 列出 SDC 库内能召回的文档名

## 场景 5:精准提问 + 高 top_k

**用户**:
> 用 top_k=10 详细搜一下 retention 相关的所有资料,我要做完整调研

**Claude 行为**:
- 调 `search_synthesis_knowledge(query="retention", top_k=10)`
- 返回更多片段,Claude 综合后给一份调研报告

## 场景 6:用错误码 ID 直接搜

**用户**:
> 1801_REF_OBJ_NOT_FOUND

**Claude 行为**:
- 检测到这是错误码格式
- 在所有库的文档标题里找匹配项
- 命中专门讲这个错误的文档,直接返回

## 场景 7:对比性问题

**用户**:
> isolation cell 和 level shifter 有什么区别?

**Claude 行为**:
- 调两次 `search_synthesis_knowledge`,分别搜两个概念
- 综合返回结果给对比说明,标注两个来源

## 反例:这些情况会被诚实告知

**用户**:
> Verilog 语法里的 always @* 怎么写?

**Claude 行为**:
- 知识库未命中(这是通用 Verilog 知识,不是芯片综合)
- 输出 `⚠️ 知识库未命中相关内容` 提示
- 然后用通用知识回答,标注"以下非知识库内容"

**用户**:
> 我们项目里 BroadwayV200 的 mem2reg 怎么处理?

**Claude 行为**:
- 项目缩写桥接:`BroadwayV200` → `BW`
- 在 memory 库里搜 `BW` 相关文档
- 如果文档库里只有 `BroadwayV100` 资料,返回相关片段并提示"未找到 V200 专门资料,以下基于 V100 经验"
