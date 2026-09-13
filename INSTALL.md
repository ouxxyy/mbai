# 安装到 Claude Code

Claude Code 会从个人目录 `~/.claude/skills/<skill-name>/SKILL.md` 或项目目录 `.claude/skills/<skill-name>/SKILL.md` 发现技能。

## 个人安装

把整个发布目录复制为：

```text
~/.claude/skills/ai-task-exposure/
```

必须保留 `SKILL.md`、`scripts/`、`docs/`、`references/` 和 `examples/drafts/` 的相对位置。若当前 Claude Code 会话启动时还没有 `~/.claude/skills/`，安装后重启一次；否则文件监听会自动发现变更。

进入 Claude Code 后运行 `/skills` 确认 `ai-task-exposure`，然后可输入：

```text
/ai-task-exposure /absolute/path/to/resume.pdf
```

也可以直接说“用这份简历做工作任务 AI 不可替代指数诊断”。

## 项目内安装

将目录复制到：

```text
<project>/.claude/skills/ai-task-exposure/
```

团队提交该目录后即可共享。官方支持的 `${CLAUDE_SKILL_DIR}` 会让脚本在个人安装、项目安装和附加目录中都能找到自身资源。

## 环境检查

在本仓库内也可以一条命令完成以下检查并给出降级提示：

```bash
python3 scripts/check_env.py
```

逐项手工命令：
python3 --version
swift --version
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version
```

最低要求是 Python 3.11。macOS 文字 PDF 解析依赖系统 PDFKit/Swift；没有 Chrome 时 HTML 仍能离线阅读并通过页面按钮导出分享卡，但命令行不会假装已经生成 PNG。
