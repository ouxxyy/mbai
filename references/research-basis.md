# 研究参考与 MBAI 的关系

核对日期：2026-09-14。固定参考以下两个指定版本，不将系列后续报告混称为本版来源。

| 来源 | 研究在看什么 | MBAI 借鉴什么 | 不能据此声称什么 |
|---|---|---|---|
| [ILO · Generative AI and Jobs: A Refined Global Index of Occupational Exposure](https://www.ilo.org/publications/generative-ai-and-jobs-refined-global-index-occupational-exposure)，2025-05-20 | 结合任务资料、从业者与专家意见、模型预测，评估职业对生成式 AI 的潜在暴露，划分四个梯度 | 先看具体任务；区分任务变化与整个岗位消失 | 四个职业梯度不能换算成个人失业概率，也不是 MBAI 的 12 类 |
| [Anthropic · The Anthropic Economic Index](https://www.anthropic.com/research/the-anthropic-economic-index)，2025-02-10 首期 | 将 Claude.ai 对话映射至 O*NET 任务，观察实际使用，区分直接完成任务与协作增强 | 具体说明 AI 接走哪些步骤、哪些步骤仍需人参与 | Claude 使用分布不代表全部劳动者、所有 AI 产品或技术能力上限；使用频率不是替代率 |

## 本工具的自建部分

任务 LOW/MEDIUM/HIGH 对应内部 0/50/100、时间权重、5 分取档、取补后的展示分、信息门槛和 12 类外号均为 MBAI 自定义。没有复现 ILO 全套职业评分，也没有接入 Anthropic 原始对话数据；模型阅读个人任务后按本地规则判断，脚本负责计算与校验。不可称为官方测评、科学认证或经研究验证的个人预测。

## 在报告里怎么用

分析沿用现有字段，无需增设关键词或研究匹配评分：`ai_can_do` 写 AI 能完成的具体步骤；`human_must_do` 写剩余的实际判断或操作；`reason` 解释为何需要这些判断，区分工具能力与公司尚未部署。不能因为尚未使用 AI 就判定安全，也不能因为使用了 AI 就判定任务已完全自动化。

上述说明是既有任务级分析口径的解释，不改变评分公式。研究不能替代用户本人的证据，不能用宏观职业数据填补其权限、成绩或工时。最终 HTML 的方法说明保留研究标题、版本日期、链接及局限；分享卡不塞入研究术语。
