"""Pure presentation renderer for a validated final report JSON."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


STYLE = r"""
:root {
  color-scheme: dark;
  --bg: #0f141c;
  --panel: #18202c;
  --panel-2: #111a26;
  --line: #2a3649;
  --text: #f0f4f8;
  --muted: #94a3b8;
  --cyan: #38bdf8;
  --green: #10b981;
  --amber: #f59e0b;
  --red: #f43f5e;
  --unknown: #64748b;
  --radius: 20px;
}
* { box-sizing: border-box; }
html { background: var(--bg); overflow-x: hidden; }
body {
  margin: 0;
  min-width: 0;
  overflow-x: hidden;
  color: var(--text);
  background:
    radial-gradient(circle at 85% 0%, rgba(56, 189, 248, .12), transparent 28rem),
    linear-gradient(rgba(42, 54, 73, .13) 1px, transparent 1px),
    linear-gradient(90deg, rgba(42, 54, 73, .13) 1px, transparent 1px),
    var(--bg);
  background-size: auto, 36px 36px, 36px 36px, auto;
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", "Segoe UI", Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
  line-height: 1.65;
  letter-spacing: .01em;
}
a { color: var(--cyan); }
.report-shell { width: min(1120px, calc(100% - 40px)); margin: 0 auto; padding: 34px 0 72px; }
.topline { display: flex; justify-content: space-between; gap: 16px; align-items: center; margin-bottom: 18px; }
.eyebrow { margin: 0; color: var(--cyan); font-size: 12px; font-weight: 800; letter-spacing: .16em; text-transform: uppercase; }
.version { color: var(--muted); font-size: 12px; }
.panel {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: linear-gradient(145deg, rgba(24,32,44,.98), rgba(17,26,38,.96));
  box-shadow: 0 24px 80px rgba(0,0,0,.24), inset 0 1px rgba(255,255,255,.035);
}
.hero { position: relative; overflow: hidden; padding: clamp(24px, 5vw, 58px); }
.hero::after { content: ""; position: absolute; width: 280px; height: 280px; border: 1px solid rgba(56,189,248,.14); border-radius: 50%; right: -90px; top: -110px; box-shadow: 0 0 90px rgba(56,189,248,.08); }
.hero-grid { display: grid; grid-template-columns: 1.25fr .75fr; gap: 42px; align-items: start; position: relative; z-index: 1; }
.role-kicker { color: var(--muted); font-size: 13px; }
h1 { margin: 8px 0 14px; font-size: clamp(34px, 6vw, 68px); line-height: 1.03; letter-spacing: -.04em; }
.tags, .task-meta { display: flex; flex-wrap: wrap; gap: 8px; }
.tag, .badge { display: inline-flex; align-items: center; min-height: 30px; padding: 5px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; border: 1px solid var(--line); color: var(--muted); background: rgba(15,20,28,.55); }
.metric { border-left: 1px solid var(--line); padding-left: 36px; }
.metric-label { color: var(--muted); font-size: 13px; }
.metric-value { margin: 8px 0 4px; font-size: clamp(46px, 7vw, 78px); font-weight: 900; line-height: 1; letter-spacing: -.05em; }
.metric-value small { color: var(--muted); font-size: 18px; letter-spacing: 0; }
.level-low { color: var(--green); } .level-medium { color: var(--amber); } .level-high { color: var(--red); } .level-unknown { color: var(--unknown); }
.confidence { margin-top: 18px; color: var(--muted); font-size: 13px; }
.declaration { margin: 30px 0 0; padding: 12px 14px; border: 1px solid rgba(56,189,248,.28); border-radius: 12px; color: #c7eefe; background: rgba(56,189,248,.07); font-size: 13px; }
.takeaways { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 24px; }
.takeaway { padding: 18px; border: 1px solid var(--line); border-radius: 14px; background: rgba(15,20,28,.54); }
.takeaway strong { display: block; margin-bottom: 8px; font-size: 13px; color: var(--cyan); }
.takeaway p { margin: 0; }
.quote { margin: 22px 0 0; padding: 22px 24px; border-left: 3px solid var(--cyan); background: rgba(56,189,248,.06); font-size: clamp(18px, 2.5vw, 25px); font-weight: 730; }
section { margin-top: 56px; scroll-margin-top: 24px; }
.section-head { display: flex; align-items: end; justify-content: space-between; gap: 20px; margin-bottom: 18px; }
.section-no { color: var(--cyan); font: 800 12px/1 ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing: .14em; }
h2 { margin: 6px 0 0; font-size: clamp(26px, 4vw, 38px); letter-spacing: -.03em; }
.section-note { max-width: 520px; margin: 0; color: var(--muted); font-size: 14px; }
.skill-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.skill-card { min-width: 0; padding: 20px; }
.skill-card h3 { margin: 0 0 16px; font-size: 15px; }
.skill-score { font-size: 34px; font-weight: 850; line-height: 1; }
.meter { height: 5px; margin: 13px 0 14px; overflow: hidden; border-radius: 99px; background: var(--line); }
.meter > span { display: block; height: 100%; background: linear-gradient(90deg, var(--cyan), #818cf8); }
.evidence { margin: 0; color: var(--muted); font-size: 13px; overflow-wrap: anywhere; }
.task-list { display: grid; gap: 14px; }
details.task { overflow: hidden; }
details.task summary { min-height: 72px; padding: 18px 22px; cursor: pointer; list-style: none; display: flex; justify-content: space-between; align-items: center; gap: 16px; }
details.task summary::-webkit-details-marker { display: none; }
.task-title { font-size: 17px; font-weight: 750; }
.task-body { border-top: 1px solid var(--line); padding: 22px; }
.task-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.machine, .human { padding: 18px; border-radius: 14px; background: rgba(15,20,28,.58); }
.machine h3, .human h3 { margin: 0 0 8px; font-size: 14px; }
.machine h3 { color: var(--cyan); } .human h3 { color: #c4b5fd; }
.reason { margin: 16px 0 0; color: var(--muted); }
.raw-evidence { margin-top: 14px; padding: 14px; border-left: 2px solid var(--line); color: #cbd5e1; background: rgba(15,20,28,.4); overflow-wrap: anywhere; }
.edge-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.edge { padding: 22px; font-size: 17px; font-weight: 650; }
.action-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.action { padding: 24px; display: flex; flex-direction: column; }
.action-label { color: var(--cyan); font: 800 12px/1 ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing: .12em; }
.action h3 { margin: 14px 0 10px; font-size: 21px; line-height: 1.25; }
.action p { color: var(--muted); }
.action dl { margin: auto 0 0; }
.action dt { margin-top: 13px; color: #cbd5e1; font-size: 12px; font-weight: 800; }
.action dd { margin: 4px 0 0; font-size: 13px; }
.share-copy { padding: 22px; margin-bottom: 18px; color: var(--muted); }
.share-export-stage { width: min(540px, calc(100% - 40px)); margin: 0 auto 56px; }
#share-card-canvas { display: block; width: 100%; height: auto; border-radius: 18px; box-shadow: 0 25px 80px rgba(0,0,0,.38); background: var(--bg); }
.download-button { width: 100%; min-height: 48px; margin-top: 14px; border: 0; border-radius: 12px; color: #06111a; background: var(--cyan); font: inherit; font-weight: 850; cursor: pointer; }
.download-button:focus-visible { outline: 3px solid white; outline-offset: 3px; }
.method { padding: 24px; }
.method p, .method li { color: var(--muted); }
.method strong { color: var(--text); }
.methodology-shell { width: min(1120px, calc(100% - 40px)); margin: 0 auto 70px; }
html.share-only, html.share-only body { width: 1080px; height: 1440px; overflow: hidden; background: #0f141c; }
html.share-only .report-shell, html.share-only .methodology-shell { display: none; }
html.share-only .share-export-stage { width: 1080px; height: 1440px; margin: 0; }
html.share-only #share-card-canvas { width: 1080px; height: 1440px; border-radius: 0; box-shadow: none; }
html.share-only .download-button { display: none; }
@media (max-width: 860px) {
  .hero-grid { grid-template-columns: 1fr; }
  .metric { border-left: 0; border-top: 1px solid var(--line); padding: 26px 0 0; }
  .skill-grid { grid-template-columns: 1fr 1fr; }
  .action-grid { grid-template-columns: 1fr; }
}
@media (max-width: 680px) {
  .report-shell, .methodology-shell { width: min(100% - 24px, 1120px); padding-top: 16px; }
  .hero { padding: 22px 18px; border-radius: 16px; }
  .topline, .section-head { align-items: flex-start; flex-direction: column; }
  .takeaways, .skill-grid, .task-columns, .edge-grid { grid-template-columns: 1fr; }
  details.task summary { min-height: 64px; padding: 15px 16px; align-items: flex-start; flex-direction: column; }
  .task-body { padding: 16px; }
  section { margin-top: 42px; }
  .download-button { min-height: 44px; }
}
@media print {
  body { background: white; color: #111827; }
  .panel { box-shadow: none; }
  .download-button { display: none; }
}
"""


CARD_SCRIPT = r"""
(() => {
  const cardData = __CARD_DATA__;
  const reportId = __REPORT_ID__;
  const params = new URLSearchParams(window.location.search);
  if (params.get("share") === "1") document.documentElement.classList.add("share-only");

  const canvas = document.getElementById("share-card-canvas");
  const ctx = canvas.getContext("2d");
  const colors = { LOW: "#10b981", MEDIUM: "#f59e0b", HIGH: "#f43f5e", UNKNOWN: "#64748b" };
  const accent = colors[cardData.exposure_level] || colors.UNKNOWN;
  const font = '-apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif';

  function roundedRect(x, y, w, h, r, fill, stroke = null) {
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, r);
    ctx.fillStyle = fill;
    ctx.fill();
    if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = 2; ctx.stroke(); }
  }

  function wrapLines(text, maxWidth, maxLines = 4) {
    const chars = Array.from(String(text));
    const lines = [];
    let line = "";
    for (const char of chars) {
      const candidate = line + char;
      if (line && ctx.measureText(candidate).width > maxWidth) {
        lines.push(line);
        line = char;
        if (lines.length === maxLines) break;
      } else {
        line = candidate;
      }
    }
    if (lines.length < maxLines && line) lines.push(line);
    if (lines.length === maxLines && chars.join("").length > lines.join("").length) {
      lines[maxLines - 1] = lines[maxLines - 1].replace(/[，。；、,.!?！？]?$/, "…");
    }
    return lines;
  }

  function drawWrapped(text, x, y, maxWidth, lineHeight, maxLines = 4) {
    const lines = wrapLines(text, maxWidth, maxLines);
    lines.forEach((line, index) => ctx.fillText(line, x, y + index * lineHeight));
    return y + lines.length * lineHeight;
  }

  function draw() {
    ctx.clearRect(0, 0, 1080, 1440);
    const bg = ctx.createLinearGradient(0, 0, 1080, 1440);
    bg.addColorStop(0, "#0f141c"); bg.addColorStop(1, "#131d2a");
    ctx.fillStyle = bg; ctx.fillRect(0, 0, 1080, 1440);
    ctx.strokeStyle = "rgba(42,54,73,.35)"; ctx.lineWidth = 1;
    for (let x = 0; x <= 1080; x += 54) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, 1440); ctx.stroke(); }
    for (let y = 0; y <= 1440; y += 54) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(1080, y); ctx.stroke(); }
    const glow = ctx.createRadialGradient(920, 80, 0, 920, 80, 420);
    glow.addColorStop(0, "rgba(56,189,248,.18)"); glow.addColorStop(1, "rgba(56,189,248,0)");
    ctx.fillStyle = glow; ctx.fillRect(500, 0, 580, 520);

    ctx.font = `700 24px ${font}`; ctx.fillStyle = "#38bdf8";
    ctx.fillText("WORK TASK // AI EXPOSURE", 72, 72);
    ctx.font = `500 22px ${font}`; ctx.fillStyle = "#94a3b8";
    ctx.textAlign = "right"; ctx.fillText(cardData.category, 1008, 72); ctx.textAlign = "left";

    ctx.font = `900 62px ${font}`; ctx.fillStyle = "#f0f4f8";
    drawWrapped(cardData.role_name, 72, 170, 900, 74, 2);
    let tagX = 72;
    ctx.font = `700 22px ${font}`;
    for (const tag of cardData.role_tags.slice(0, 3)) {
      const width = ctx.measureText(tag).width + 40;
      roundedRect(tagX, 246, width, 44, 22, "rgba(15,20,28,.72)", "#2a3649");
      ctx.fillStyle = "#cbd5e1"; ctx.fillText(tag, tagX + 20, 276); tagX += width + 12;
    }

    roundedRect(72, 326, 936, 230, 26, "rgba(24,32,44,.94)", "#2a3649");
    ctx.font = `800 24px ${font}`; ctx.fillStyle = "#94a3b8";
    ctx.fillText("工作任务 AI 暴露指数", 112, 378);
    const indexText = cardData.exposure_index === null ? "信息不足" : String(cardData.exposure_index);
    ctx.font = cardData.exposure_index === null ? `900 74px ${font}` : `900 134px ${font}`;
    ctx.fillStyle = accent; ctx.fillText(indexText, 110, cardData.exposure_index === null ? 480 : 505);
    if (cardData.exposure_index !== null) {
      ctx.font = `700 30px ${font}`; ctx.fillStyle = "#64748b"; ctx.fillText("/ 100", 340, 493);
    }
    ctx.font = `650 22px ${font}`; ctx.fillStyle = "#cbd5e1"; ctx.textAlign = "right";
    ctx.fillText(cardData.confidence_label, 964, 382);
    ctx.fillStyle = accent; ctx.fillText(cardData.exposure_level, 964, 426); ctx.textAlign = "left";

    roundedRect(72, 586, 936, 188, 24, "rgba(56,189,248,.075)", "rgba(56,189,248,.32)");
    ctx.font = `800 33px ${font}`; ctx.fillStyle = "#f0f4f8";
    drawWrapped(`“${cardData.snarky_quote}”`, 112, 646, 856, 46, 3);

    ctx.font = `800 22px ${font}`; ctx.fillStyle = "#38bdf8"; ctx.fillText("人机任务切片", 72, 834);
    cardData.task_highlights.slice(0, 2).forEach((item, index) => {
      const y = 866 + index * 142;
      roundedRect(72, y, 936, 124, 18, "rgba(24,32,44,.92)", "#2a3649");
      ctx.font = `800 25px ${font}`; ctx.fillStyle = "#f0f4f8"; ctx.fillText(item.task_name, 102, y + 40);
      ctx.font = `600 20px ${font}`; ctx.fillStyle = "#38bdf8";
      drawWrapped(`AI：${item.ai_part}`, 102, y + 76, 400, 28, 2);
      ctx.fillStyle = "#c4b5fd";
      drawWrapped(`人：${item.human_part}`, 548, y + 76, 420, 28, 2);
    });

    roundedRect(72, 1168, 936, 130, 20, "rgba(245,158,11,.08)", "rgba(245,158,11,.36)");
    ctx.font = `800 21px ${font}`; ctx.fillStyle = "#f59e0b"; ctx.fillText("7 天证明动作", 102, 1208);
    ctx.font = `750 27px ${font}`; ctx.fillStyle = "#f0f4f8";
    drawWrapped(cardData.proof_7d, 102, 1250, 846, 36, 2);

    ctx.font = `600 19px ${font}`; ctx.fillStyle = "#94a3b8";
    drawWrapped(cardData.disclaimer, 72, 1360, 936, 28, 2);
    ctx.textAlign = "right"; ctx.fillStyle = "#64748b"; ctx.fillText("已脱敏分享卡", 1008, 1402); ctx.textAlign = "left";
    window.__CARD_READY__ = true;
  }

  function updateLayoutProbe() {
    const root = document.documentElement;
    root.setAttribute("data-horizontal-overflow", String(root.scrollWidth > window.innerWidth));
    root.setAttribute("data-viewport-width", String(window.innerWidth));
    root.setAttribute("data-scroll-width", String(root.scrollWidth));
  }

  draw(); updateLayoutProbe();
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => { draw(); updateLayoutProbe(); });
  window.addEventListener("resize", updateLayoutProbe);
  document.getElementById("download-card").addEventListener("click", () => {
    canvas.toBlob((blob) => {
      if (!blob) return;
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `${reportId}-share-card.png`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(link.href), 1000);
    }, "image/png");
  });
})();
"""


SKILL_LABELS = {
    "execution": "任务执行",
    "discretion": "判断决策",
    "coordination": "协作协调",
    "accountability": "责任承担",
}
ACTION_LABELS = {"hand_to_ai": "交给 AI", "level_up": "强化自己", "proof_7d": "拿出证据"}
LEVEL_LABELS = {"LOW": "低暴露", "MEDIUM": "中暴露", "HIGH": "高暴露", "UNKNOWN": "未知"}


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _json_for_script(value: Any) -> str:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _skill_card(name: str, item: dict[str, Any]) -> str:
    known = bool(item.get("is_known"))
    score = item.get("score") if known else None
    value = f"{score}" if score is not None else "未知"
    width = max(0, min(100, int(score or 0)))
    return f"""
      <article class="skill-card panel">
        <h3>{_e(SKILL_LABELS[name])}</h3>
        <div class="skill-score">{_e(value)}{f'<small> / 100</small>' if score is not None else ''}</div>
        <div class="meter" aria-hidden="true"><span style="width:{width}%"></span></div>
        <p class="evidence">{_e(item.get('evidence') or '简历未提及')}</p>
      </article>"""


def _task_card(task: dict[str, Any]) -> str:
    level = task["exposure_level"]
    time_label = f"时间占比 {_e(task['time_share_percent'])}%" if task.get("time_share_percent") is not None else "等权"
    return f"""
      <details class="task panel">
        <summary>
          <span class="task-title">{_e(task['task_name'])}</span>
          <span class="task-meta">
            <span class="badge level-{level.lower()}">{_e(LEVEL_LABELS[level])}</span>
            <span class="badge">{time_label}</span>
            <span class="badge">证据 {_e(task['confidence'])}</span>
          </span>
        </summary>
        <div class="task-body">
          <div class="task-columns">
            <div class="machine"><h3>🤖 AI 能接手</h3><div>{_e(task['ai_can_do'])}</div></div>
            <div class="human"><h3>🧑 你仍需负责</h3><div>{_e(task['human_must_do'])}</div></div>
          </div>
          <p class="reason"><strong>判断理由：</strong>{_e(task['reason'])}</p>
          <div class="raw-evidence"><strong>证据原文：</strong>{_e(task['evidence'])}</div>
        </div>
      </details>"""


def _action_card(kind: str, action: dict[str, Any]) -> str:
    return f"""
      <article class="action panel">
        <div class="action-label">{_e(ACTION_LABELS[kind])}</div>
        <h3>{_e(action['title'])}</h3>
        <p>{_e(action['action'])}</p>
        <dl>
          <dt>交付物</dt><dd>{_e(action['deliverable'])}</dd>
          <dt>完成标准</dt><dd>{_e(action['acceptance_criteria'])}</dd>
          <dt>人工检查点</dt><dd>{_e(action['human_checkpoint'])}</dd>
          <dt>经历依据</dt><dd>{_e(action['grounded_evidence'])}</dd>
        </dl>
      </article>"""


def render_report(report: dict[str, Any]) -> str:
    """Render exactly what final JSON says; scoring belongs upstream."""
    metadata = report["report_metadata"]
    profile = report["profile"]
    role = profile["role"]
    metrics = report["metrics"]
    index = metrics["exposure_index"]
    level = metrics["exposure_level"]
    index_attr = "unknown" if index is None else str(index)
    metric_value = "信息不足" if index is None else f"{index} <small>/ 100</small>"
    metric_aria = "信息不足" if index is None else f"{index} / 100"

    evaluable = [task for task in report["tasks"] if task["exposure_level"] != "UNKNOWN"]
    affected = sorted(
        evaluable,
        key=lambda task: (task.get("score", -1), task.get("time_share_percent") or 0),
        reverse=True,
    )[:2]
    affected_text = "；".join(f"{item['task_name']}（{LEVEL_LABELS[item['exposure_level']]}）" for item in affected) or "现有证据不足，暂不判断受影响任务。"
    edge_text = report["human_edge"][0]["summary"]

    tags = "".join(f'<span class="tag">{_e(tag)}</span>' for tag in role["tags"])
    skills = "".join(_skill_card(name, report["skill_panel"][name]) for name in SKILL_LABELS)
    tasks = "".join(_task_card(task) for task in report["tasks"])
    edges = "".join(f'<article class="edge panel">{_e(point["summary"])}</article>' for point in report["human_edge"])
    actions = "".join(_action_card(kind, report["action_plan"][kind]) for kind in ACTION_LABELS)
    sources = "".join(
        f'<li><strong>{_e(source["organization"])}</strong>：<a href="{_e(source["url"])}" target="_blank" rel="noreferrer">{_e(source["title"])}</a>（发布 {_e(source["publication_date"])}；访问 {_e(source["accessed_at"])}）。{_e(source["boundary"])}</li>'
        for source in report["methodology"]["sources"]
    )

    card_script = (
        CARD_SCRIPT.replace("__CARD_DATA__", _json_for_script(report["share_card"]))
        .replace("__REPORT_ID__", _json_for_script(metadata["report_id"]))
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="color-scheme" content="dark">
  <title>{_e(role['name'])}｜工作任务 AI 暴露指数</title>
  <style>{STYLE}</style>
</head>
<body>
  <main class="report-shell">
    <div class="topline"><p class="eyebrow">Career Audit // {_e(profile['sanitized_category'])}</p><span class="version">规则 v{_e(report['rule_version'])}</span></div>
    <section id="hero" class="hero panel">
      <div class="hero-grid">
        <div>
          <div class="role-kicker">你的职场游戏角色</div>
          <h1>{_e(role['name'])}</h1>
          <div class="tags">{tags}</div>
        </div>
        <div class="metric" data-exposure-index="{_e(index_attr)}">
          <div class="metric-label">工作任务 AI 暴露指数</div>
          <div class="metric-value level-{level.lower()}" aria-label="{_e(metric_aria)}">{metric_value}</div>
          <span class="badge level-{level.lower()}">{_e(LEVEL_LABELS[level])}</span>
          <div class="confidence">证据置信度：{_e(metadata['confidence_level'])}<br>{_e(metadata['confidence_reason'])}</div>
        </div>
      </div>
      <div class="takeaways">
        <div class="takeaway"><strong>最受影响任务</strong><p>{_e(affected_text)}</p></div>
        <div class="takeaway"><strong>你仍然值钱的地方</strong><p>{_e(edge_text)}</p></div>
      </div>
      <blockquote class="quote">“{_e(role['snarky_quote'])}”</blockquote>
      <p class="declaration">工作任务 AI 暴露指数自测 · 基于具体任务证据 · 本工具自建规则 · 不是失业概率预测</p>
    </section>

    <section id="skill-panel">
      <div class="section-head"><div><span class="section-no">01 // ATTRIBUTES</span><h2>技能面板</h2></div><p class="section-note">四项只显示简历与补问中实际出现的证据；未知不是零分。</p></div>
      <div class="skill-grid">{skills}</div>
    </section>

    <section id="task-breakdown">
      <div class="section-head"><div><span class="section-no">02 // TASK ANATOMY</span><h2>人机任务拆解</h2></div><p class="section-note">展开每项任务，查看 AI 能做什么、你仍需负责什么，以及原文依据。</p></div>
      <div class="task-list">{tasks}</div>
    </section>

    <section id="human-edge">
      <div class="section-head"><div><span class="section-no">03 // HUMAN EDGE</span><h2>个人价值</h2></div><p class="section-note">AI 介入之后，值得保留和强化的具体贡献。</p></div>
      <div class="edge-grid">{edges}</div>
    </section>

    <section id="action-plan">
      <div class="section-head"><div><span class="section-no">04 // NEXT MOVES</span><h2>三个升级动作</h2></div><p class="section-note">全部来自你的任务证据，且有交付物、检查点和完成标准。</p></div>
      <div class="action-grid">{actions}</div>
    </section>

    <section id="share-export">
      <div class="section-head"><div><span class="section-no">05 // SHARE</span><h2>脱敏分享卡</h2></div><p class="section-note">PNG 只使用独立的脱敏字段，不包含姓名、联系方式、公司、学校、客户、项目名或完整简历。</p></div>
      <div class="share-copy panel">下方卡片由浏览器原生 Canvas 生成。点击按钮会在本机导出严格 1080 × 1440 的 PNG，无需联网。</div>
    </section>
  </main>

  <div class="share-export-stage">
    <canvas id="share-card-canvas" width="1080" height="1440" aria-label="脱敏职业诊断分享卡"></canvas>
    <button id="download-card" class="download-button" type="button">保存 1080 × 1440 脱敏卡</button>
  </div>

  <footer id="methodology" class="methodology-shell">
    <div class="method panel">
      <span class="section-no">06 // METHOD &amp; BOUNDARY</span><h2>方法与边界</h2>
      <p><strong>{_e(report['methodology']['custom_rules_disclaimer'])}</strong></p>
      <ul>{sources}</ul>
    </div>
  </footer>
  <script>{card_script}</script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Final report JSON")
    parser.add_argument("--output", required=True, type=Path, help="Offline HTML report")
    args = parser.parse_args()
    report = json.loads(args.input.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_report(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
