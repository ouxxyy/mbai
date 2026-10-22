# MBAI · 工作任务 AI 不可替代指数｜任务分析与替代风险自评

提供简历、工作总结或任务描述，MBAI 会拆解工作中的自动化空间、个人贡献和证据缺口，输出解释性自评与行动建议；Skill 路径可生成离线报告。它用于职业反思，不预测失业或裁员。

MBAI（Me, Beyond AI · 我，在 AI 之上）是测评品牌名；正式指标名是「工作任务 AI 不可替代指数」——分数越高，说明你的工作越依赖你本人。

[使用示例](#quick-example) · [开始使用](#quick-start) · [English](#english-overview)

<a id="quick-example"></a>

## 一次使用示例

**虚构输入：** 后端开发的工作由写 API（45%）、测试与文档（25%）、值班处理生产故障（30%）组成。

**输出：** 分析哪些任务可先由 AI 接手、哪些判断仍需要本人，以及应补哪些贡献证据。仓库合成案例的报告和脱敏分享卡见 [结果示例](#结果示例)，该案例分数不代表你的结果。

[两种用法](#quick-start) 中，Prompt 给估算结果，Skill 使用本地脚本复算。

## 适用人群

你在互联网行业工作了 0–8 年，正在想跳槽涨薪。这个工具帮你用 AI 改造现有的工作，看清哪些贡献属于你本人，最后整理成能带去面试的作品。

只要手头有近期的工作材料就能用：简历、年终总结，或者几段描述自己工作的文字。人群口径只说明它为谁设计；评分只看任务，不看年限、岗位名称或个人属性。

## 它解决什么问题

跳槽的时候，多数人说不清自己真正的贡献：哪些活 AI 已经能接手，哪些离不开你，简历和面试里都拿不出证据。

这个工具把你的工作拆到任务级，逐条给出判断：AI 能接手哪些步骤，你的贡献和证据缺口在哪，先改造哪一项任务，怎么留下可检查的求职证据。评分由本地脚本完成，同一份输入永远得到同一个分数。

## 结果示例

下图由仓库内的虚构案例生成，不含任何真实个人信息。案例是一名后端开发，工作有三块：写 API 占 45%，测试与文档占 25%，值班处理生产故障占 30%。

<p align="center">
  <img src="assets/demo/report-sample-top.png" alt="离线 HTML 报告首屏：上线守门员，不可替代指数 50，中不可替代，AI 能接手哪些、哪些还得你管" width="560">
  <br>
  <img src="assets/demo/share-card-sample.png" alt="脱敏分享卡：MBAI 品牌、角色形象、指数 50 与中不可替代等级、一句话金句" width="420">
</p>

这份报告的结论是：不可替代指数 50，中不可替代；优先改造的是那 25% 的测试与文档任务，它边界清楚、结果可验证，改造过程本身就是第一份求职作品的素材。三个行动连成一条路径：改造任务、练习关键判断、留下求职证据，第 7 天有第一个可检查的进展。

<a id="quick-start"></a>

## 两种用法

### 方式一：复制提示语，不用安装

打开仓库根目录的 PROMPT.md，全文复制，粘贴到任意 AI 对话框，再按提示贴上你的工作材料。提示语会引导 AI 补问，最多 3 个问题，可以跳过，最后输出任务拆解、贡献缺口和三个行动。这条路径的指数是估算，未经本地脚本校验，提示语里会明确标注。

### 方式二：安装 Skill，完整版

任何支持 Agent Skills 格式（`SKILL.md`）的 agent 工具都能用。以 Claude Code 为例，把仓库复制为个人技能目录：

```bash
git clone https://github.com/ouxxyy/mbai.git
mkdir -p ~/.claude/skills
cp -R mbai ~/.claude/skills/ai-task-exposure
```

其他工具放进各自的技能目录（如 ZCode 的 `~/.zcode/skills/`、通用的 `~/.agents/skills/`），保持仓库目录结构原样即可。重启或重新加载技能后，直接对 agent 说：

```text
用这份材料做工作任务 AI 不可替代指数诊断：<文件路径>
```

Claude Code 里也可以输入 `/mbai /absolute/path/to/resume.pdf`。

环境要求：任何装有 Python 3.11+ 的电脑，macOS、Windows、Linux 均可。唯一平台差异是文件型 PDF 的解析，macOS 用系统自带的 PDFKit，其他平台改用 DOCX / TXT / MD 或直接粘贴文本，评分与渲染完全一致。可以用一条命令检查环境：

```bash
python3 scripts/check_env.py
```

## 它怎么工作

1. 安装 Skill 到你的 agent 工具（见上方方式二）。
2. 给它一份文字型 PDF、DOCX，或直接粘贴文本。简历、年度工作总结、一段关于自己工作的描述，都可以。
3. Claude 按冻结规则拆解任务并逐条评估；信息不足时最多补问 3 个问题，跳过就降低置信度继续。
4. 本地脚本完成契约校验、评分和渲染，产出离线 HTML 报告与 PNG 分享卡。命令行导出 PNG 需要 Chrome；没有 Chrome 时也可以直接在 HTML 页面里点按钮导出。

报告会告诉你：总指数与等级（低 / 中 / 高不可替代）、12 类工作方式角色（如「职场拆弹专家」）、AI 能接手哪些任务、哪些还得你管、以及 7 天内可启动的行动。卡片只保留脱敏后的身份与结论，适合直接发朋友圈或社群。

## 开发者命令

运行完整测试（标准库 `unittest`，零第三方运行时依赖）：

```bash
python3 -m unittest discover -s tests -v
```

从 draft JSON 构建全套产物（最终 JSON、离线 HTML、PNG）：

```bash
python3 -m scripts.build_report --draft examples/drafts/risk-owner-showcase.json --output-dir examples/output/demo
```

版本单一来源在 `scripts/version.py`（当前 5.1.0）；冻结规则见 `docs/`，中间 JSON Schema 见 `references/`。

## 口径与边界

- 展示分 = 100 − 取整后替代分，唯一换算口径为先取整、后取补；分数越高越依赖本人。
- 这是本工具的自建解释性评分，不是失业概率、裁员预测，也不是任何研究机构的个人认证。研究设计参考了 ILO 的任务暴露视角与 Anthropic 首期实际使用观察，详见 [研究依据](references/research-basis.md)。
- 信息不足标 `UNKNOWN`，不当作低风险；可判断任务不足一半时不显示总指数。
- 扫描件、图片型 PDF、乱码或空文本不做猜测式 OCR，会明确请求文字版。
- 分享卡只能使用脱敏字段：姓名、联系方式、公司、学校、客户、项目名命中隐私门禁时必须返工。
- 渲染器只消费已验证的最终 JSON，不在 HTML 阶段重新分析。
- 请勿向本仓库提交真实简历；`examples/` 中全部为虚构验收数据。

## 常见问题

### 这个分数能预测我会不会被裁吗？

不能。这是自建、解释性的任务级评分，不是失业概率、裁员预测或个人价值判定。

### 复制 Prompt 和安装 Skill 有什么区别？

Prompt 路径给出未经过本地脚本校验的估算；Skill 路径按照冻结规则由本地脚本评分并生成报告。

### 报告离线打开，分析也完全离线吗？

离线描述的是报告浏览。材料如何被模型处理取决于所用宿主，不能因此推断分析全在本地。

### 可以商用或随意处理 PDF 吗？

项目采用 CC BY-NC 4.0，需署名且不可商用。文件型 PDF 的解析依赖 macOS PDFKit；其他系统使用 DOCX/TXT/MD 或粘贴文本。

<a id="english-overview"></a>

## English overview

MBAI is a task-level AI assessment for career reflection. It identifies automatable work, personal contributions and evidence gaps, with an offline report and a redacted sharing card. The index is an explanatory rubric, not a prediction of layoffs or unemployment.

Choose the [Prompt or Skill workflow](#quick-start). Prompt results are estimates; the Skill uses deterministic local scoring. Python 3.11+ is required for scripts, and file-based PDF extraction uses macOS PDFKit. Licensed under CC BY-NC 4.0: attribution is required and commercial use is not permitted.

## 相关项目

[欧八同学的 AI Skills 与跳槽涨薪工具合集](https://github.com/ouxxyy/ouba-classmate)，还可以接着使用：

- [把已有贡献证据整理进简历](https://github.com/ouxxyy/jd-resume-match)
- [练习讲清个人贡献](https://github.com/ouxxyy/ai-interviewer)

## 作者

作者全平台同名：**欧八同学**。

- 个人主页 / 联系我：[albertou.redboook.cn](https://albertou.redboook.cn/)
- 微信公众号：扫码关注
- 抖音：[搜索"欧八同学"](https://www.douyin.com/search/%E6%AC%A7%E5%85%AB%E5%90%8C%E5%AD%A6)
- 小红书：[搜索"欧八同学"](https://www.xiaohongshu.com/search_result?keyword=%E6%AC%A7%E5%85%AB%E5%90%8C%E5%AD%A6)
- X：[搜索"欧八同学"](https://x.com/search?q=%E6%AC%A7%E5%85%AB%E5%90%8C%E5%AD%A6&src=typed_query)

<p align="center">
  <img src="assets/wechat-qr.jpg" alt="欧八同学微信公众号二维码" width="260">
</p>

如果这个项目对你有用，欢迎点个 Star。遇到问题时，提交命令、报错和最小复现步骤就够了；请不要上传真实私人照片或简历。

## 许可证

本项目以 [CC BY-NC 4.0](LICENSE)（署名—非商业性使用 4.0 国际）协议发布：

- **不可商用**：不得将本项目或其改编版本用于商业目的（出售、付费服务、商业产品内置等）。
- **需保留原作者信息**：分享或修改本项目时，必须署名「欧八同学 / MBAI」、保留 LICENSE 文件，并注明原项目地址与是否修改过内容。
- MBAI 标识、角色形象与公众号二维码仅用于本项目原作者署名，移除或替换后不得再以 MBAI 名义分发。
