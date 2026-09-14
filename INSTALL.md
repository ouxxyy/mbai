# 安装到你的 agent 工具

本技能是标准的 Agent Skills 格式（`SKILL.md` + 随附脚本），任何支持该格式的 agent 工具都能使用。各工具的技能发现目录不同：Claude Code 读取个人目录 `~/.claude/skills/<skill-name>/SKILL.md` 或项目目录 `.claude/skills/<skill-name>/SKILL.md`；ZCode 等其他工具按其文档放置（如 `~/.zcode/skills/`、`~/.agents/skills/`）。

## 个人安装

把整个仓库复制为你所用工具的个人技能目录。以 Claude Code 为例：

```text
~/.claude/skills/ai-task-exposure/
```

必须保留 `SKILL.md`、`scripts/`、`docs/`、`references/` 和 `examples/drafts/` 的相对位置。若工具只在启动时扫描技能目录，安装后重启一次即可被发现。

进入 Claude Code 后运行 `/skills` 确认 `ai-task-exposure`，然后可输入：

```text
/mbai /absolute/path/to/resume.pdf
```

在其他工具里，直接说「用这份材料做工作任务 AI 不可替代指数诊断」并附上文件路径或粘贴文本。

## 项目内安装

将目录复制到：

```text
<project>/.claude/skills/ai-task-exposure/
```

团队提交该目录后即可共享。Claude Code 官方支持的 `${CLAUDE_SKILL_DIR}` 会让脚本在个人安装、项目安装和附加目录中都能找到自身资源；其他工具按各自约定让脚本以技能目录为基准定位。

## 输入材料

不限于简历。年度工作总结、述职材料、或一段描述自己日常工作的文字都可以，也可以直接在对话里粘贴文字。技能会从中提取具体工作任务，再逐条评估。

## 环境检查

在本仓库内也可以一条命令完成环境检查并给出降级提示：

```bash
python3 scripts/check_env.py
```

最低要求是 Python 3.11，macOS、Windows、Linux 均可。唯一的平台差异是文件型 PDF 的解析：macOS 使用系统自带的 PDFKit/Swift；其他平台请改用 DOCX、TXT、MD 或直接粘贴文本，评分与渲染完全一致。没有 Chrome 时 HTML 仍能离线阅读并通过页面按钮导出分享卡，但命令行不会假装已经生成 PNG。
