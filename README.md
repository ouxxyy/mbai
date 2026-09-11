# 工作任务 AI 暴露指数 Skill

一个可安装到 Claude Code 的中文职业诊断 Skill。它从文字型 PDF、DOCX 或粘贴文本中提取工作任务，在最多三次按需补问后，生成离线 HTML 报告和 1080 × 1440 脱敏 PNG 分享卡。

正式指标是“工作任务 AI 暴露指数”：这是本项目的解释性自建评分，不是失业概率，也不是任何研究机构对个人的预测。

## 当前状态

分析规则与中间数据接口已冻结；实现代码将在该契约之上逐项补齐。渲染器只能消费结构化结果，不得重新推断分数、角色或行动建议。

## 技术与目录

- Python 3.11+：简历提取、契约校验、评分、HTML 生成和验收脚本；无第三方 Python 运行时依赖。
- macOS PDFKit（Swift 桥接）：解析文字型 PDF；扫描件明确回退文字版。
- 原生 HTML/CSS/JavaScript：单文件离线报告与 Canvas 分享卡下载。
- Chrome/Chromium：命令行 PNG 实际导出；HTML 本身无需浏览器扩展或在线资源。
- `docs/`：冻结规则、接口和研究边界。
- `references/`：中间 JSON Schema。
- `scripts/`：后续实现入口。
- `templates/`：内嵌报告模板。
- `tests/`：标准库 `unittest` 测试。
- `examples/`：虚构简历、结构化分析及生成结果。

## 安装与命令

依赖安装、报告生成、完整验收命令会随实现一并补入。目前可运行：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
python3 -m unittest discover -s tests -v
```

当前未配置 Lint、独立类型检查、部署或 CI。首版不建设在线网站。

## 已知边界

- 扫描件、图片型 PDF、乱码或空文本不会做猜测式 OCR；会明确请求文字版。
- 任务拆解与补问由 Claude Code 按 `SKILL.md` 执行，确定性脚本负责校验、聚合、渲染和隐私门禁。
- 研究来源只提供设计参考，不构成机构认证或个人预测。
