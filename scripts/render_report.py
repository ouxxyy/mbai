"""Pure presentation renderer for a validated final report JSON.

B 方向（新瑞士式黑黄撞色态度海报）呈现，规范：docs/DESIGN_SYSTEM_B_POSTER.md。
渲染器只消费最终 JSON；角色素材按 ROLE_TABLE 解析为 data URI 内嵌，
每份报告只内嵌主角色（或神秘工）＋神秘工兜底两张，断网可看、可导出。
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.role_match import ROLE_BY_CODE, SHADOW_WORKER

ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "characters"
BRAND_BADGE_PNG = Path(__file__).resolve().parents[1] / "assets" / "brand" / "png" / "mbai_badge_64px.png"
BRAND_LOCKUP = "mbai — Me, Beyond AI · 我，在 AI 之上"

# 3.0.0 词表拆分：汇总位说「不可替代」，任务行说「AI 可接管」——同一页面不允许同词反义。
SUMMARY_LEVEL_LABELS = {"LOW": "低不可替代", "MEDIUM": "中不可替代", "HIGH": "高不可替代", "UNKNOWN": "未知"}
TASK_LEVEL_LABELS = {"LOW": "AI 可接管·少量", "MEDIUM": "AI 可接管·部分", "HIGH": "AI 可接管·大部分", "UNKNOWN": "未知"}
SKILL_LABELS = {
    "execution": "任务执行",
    "discretion": "判断决策",
    "coordination": "协作协调",
    "accountability": "责任承担",
}
ACTION_LABELS = {"hand_to_ai": "交给 AI", "level_up": "强化自己", "proof_7d": "拿出证据"}


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


def _asset_data_uri(filename: str) -> str:
    path = ASSET_DIR / filename
    if not path.is_file():
        raise RuntimeError(f"角色素材缺失，拒绝渲染缺角色的报告：{path}")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/webp;base64,{encoded}"


def _brand_badge_data_uri() -> str:
    if not BRAND_BADGE_PNG.is_file():
        raise RuntimeError(f"品牌徽章缺失，拒绝渲染缺标的报告：{BRAND_BADGE_PNG}")
    encoded = base64.b64encode(BRAND_BADGE_PNG.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _role_assets(report: dict[str, Any]) -> dict[str, str]:
    """只内嵌主角色（或神秘工）＋神秘工兜底。"""
    code = report["profile"]["role"]["code"]
    main = ROLE_BY_CODE.get(code, SHADOW_WORKER)
    assets = {"main": _asset_data_uri(main["asset"])}
    if main["code"] != SHADOW_WORKER["code"]:
        assets["shadow"] = _asset_data_uri(SHADOW_WORKER["asset"])
    else:
        assets["shadow"] = assets["main"]
    assets["badge"] = main["badge"]
    assets["code"] = main["code"]
    assets["definition"] = main["definition"]
    assets["brand_badge"] = _brand_badge_data_uri()
    return assets


STYLE = r"""
:root {
  --c-yellow: #EBFB3B;
  --c-black: #0D0D0D;
  --c-orange: #FF4A00;
  --c-gray-light: #F4F4F0;
  --c-white: #FFFFFF;
  --c-dark-card: #1A1A1A;
  --c-border: #0D0D0D;
  --font-heavy: "Impact", "Arial Black", -apple-system, BlinkMacSystemFont, "PingFang SC", "Heiti SC", sans-serif;
  --font-sans: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  --font-mono: "SF Mono", "Consolas", "Monaco", "Courier New", monospace;
  color-scheme: light;
}
* { box-sizing: border-box; min-width: 0; }
html { background: var(--c-gray-light); overflow-x: hidden; }
body {
  margin: 0;
  min-width: 0;
  overflow-x: hidden;
  color: var(--c-black);
  background: var(--c-gray-light);
  font-family: var(--font-sans);
  line-height: 1.65;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}
a { color: var(--c-black); text-decoration: underline; }
.report-shell { width: min(1160px, calc(100% - 40px)); margin: 0 auto; padding: 30px 0 70px; }
.poster-ticker {
  display: flex; flex-wrap: wrap; gap: 6px 18px; align-items: center; justify-content: space-between;
  min-height: 44px; padding: 8px 16px; margin-bottom: 22px;
  background: var(--c-black); color: var(--c-yellow);
  font: 700 13px/1.35 var(--font-mono); letter-spacing: .06em;
}
.poster-ticker .ticker-secondary { color: var(--c-gray-light); }
.ticker-brand { display: inline-flex; align-items: center; gap: 8px; font: 900 15px/1 var(--font-heavy); letter-spacing: .04em; color: var(--c-yellow); }
.ticker-badge { width: 26px; height: 26px; display: block; border: 2px solid var(--c-yellow); }
.brand-lockup { margin: 18px 0 0; padding-top: 14px; border-top: 3px solid var(--c-black); font: 700 14px/1.5 var(--font-mono); letter-spacing: .02em; }
.hero-grid { display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 28px; align-items: stretch; }
.attitude-block {
  position: relative; display: flex; flex-direction: column; justify-content: flex-end;
  padding: 34px 34px 30px;
  background: var(--c-black); color: var(--c-white);
  border: 3.5px solid var(--c-border); box-shadow: 10px 10px 0 rgba(0,0,0,.15);
}
.attitude-index-row { display: flex; align-items: flex-end; gap: 18px; flex-wrap: wrap; }
.giant-index {
  font-family: var(--font-heavy); font-weight: 900; font-size: 168px; line-height: .82;
  color: var(--c-yellow); letter-spacing: -.02em;
}
.giant-index.unknown { font-size: 96px; line-height: 1; padding-bottom: 10px; }
.level-chip {
  display: inline-block; margin-bottom: 14px; padding: 8px 18px;
  background: var(--c-orange); color: var(--c-black);
  border: 3px solid var(--c-black); box-shadow: 6px 6px 0 rgba(235,251,59,.35);
  font: 900 40px/1 var(--font-heavy); letter-spacing: .02em;
}
.level-chip.level-HIGH { background: var(--c-yellow); box-shadow: 6px 6px 0 rgba(13,13,13,.35); }
.level-chip.level-unknown { background: var(--c-gray-light); }
.index-caption { margin: 14px 0 0; color: var(--c-gray-light); font-size: 14px; }
.character-title {
  margin: 26px 0 0; font: 900 34px/1.2 var(--font-sans); color: var(--c-white);
  overflow-wrap: anywhere;
}
.character-definition { margin: 8px 0 0; color: var(--c-gray-light); font-size: 16px; }
.snarky-banner {
  margin: 22px 0 0; padding: 16px 20px; transform: rotate(-.5deg);
  background: var(--c-yellow); color: var(--c-black);
  border: 3.5px solid var(--c-black); box-shadow: 8px 8px 0 rgba(0,0,0,.35);
  font: 900 26px/1.35 var(--font-heavy); overflow-wrap: anywhere;
}
.stage-block {
  display: flex; flex-direction: column; align-items: center; justify-content: space-between;
  padding: 22px; background: var(--c-yellow); border: 3.5px solid var(--c-border);
  box-shadow: 10px 10px 0 rgba(0,0,0,.15);
}
.specimen-capsule {
  align-self: stretch; display: flex; flex-wrap: wrap; gap: 4px 12px; justify-content: space-between;
  padding: 8px 14px; background: var(--c-black); color: var(--c-yellow);
  font: 700 13px/1.4 var(--font-mono);
}
.character-stage {
  position: relative; width: 100%; margin: 14px 0; padding: 22px 16px 18px;
  background: var(--c-white); border: 3.5px solid var(--c-black);
  border-radius: 16px; box-shadow: 6px 6px 0 var(--c-black);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  overflow: hidden;
}
.character-figure {
  position: relative; z-index: 2; width: min(380px, 100%); height: auto; display: block;
  filter: drop-shadow(0 10px 18px rgba(0,0,0,.15));
}
.character-plinth {
  position: relative; z-index: 1; width: 68%; height: 22px; margin-top: -16px;
  background: radial-gradient(ellipse at center, #2b2b2b 0%, var(--c-black) 100%);
  border-radius: 50%; box-shadow: 0 4px 8px rgba(0,0,0,.35);
}
.stage-nameplate {
  align-self: stretch; margin-top: 18px; padding: 14px 18px; background: var(--c-white);
  border: 3px solid var(--c-black); font-size: 14px;
}
.stage-nameplate strong { display: block; margin-bottom: 4px; font-size: 15px; }
.situation-paper {
  margin-top: 28px; padding: 26px 30px; background: var(--c-white);
  border: 3.5px solid var(--c-black); box-shadow: 10px 10px 0 rgba(0,0,0,.15);
}
.situation-paper p { margin: 0; font-size: 16px; line-height: 1.65; overflow-wrap: anywhere; }
.takeaway-row { display: grid; grid-template-columns: 1fr 1fr; gap: 28px; margin-top: 28px; }
.takeaway { padding: 18px 20px; background: var(--c-white); border: 3px solid var(--c-black); box-shadow: 8px 8px 0 rgba(0,0,0,.12); }
.takeaway strong { display: block; margin-bottom: 8px; font: 700 13px/1.2 var(--font-mono); letter-spacing: .08em; }
.takeaway p { margin: 0; font-size: 15px; overflow-wrap: anywhere; }
section { margin-top: 56px; scroll-margin-top: 24px; }
.section-head { display: flex; align-items: end; justify-content: space-between; gap: 20px; margin-bottom: 18px; }
.section-no { color: var(--c-black); font: 800 13px/1 var(--font-mono); letter-spacing: .14em; }
h2 { margin: 6px 0 0; font: 900 28px/1.3 var(--font-sans); letter-spacing: -.01em; }
.section-note { max-width: 540px; margin: 0; font-size: 14px; overflow-wrap: anywhere; }
.skill-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.skill-card { padding: 18px; background: var(--c-white); border: 3px solid var(--c-black); box-shadow: 8px 8px 0 rgba(0,0,0,.12); }
.skill-card h3 { margin: 0 0 12px; font-size: 15px; }
.skill-score { font: 900 34px/1 var(--font-heavy); }
.skill-score small { font: 700 13px/1 var(--font-sans); }
.skill-meter { height: 8px; margin: 12px 0; background: var(--c-gray-light); border: 2px solid var(--c-black); }
.skill-meter > span { display: block; height: 100%; background: var(--c-orange); }
.skill-evidence { margin: 0; font-size: 13px; overflow-wrap: anywhere; }
.task-list { display: grid; gap: 16px; }
details.task { background: var(--c-white); border: 3px solid var(--c-black); box-shadow: 8px 8px 0 rgba(0,0,0,.12); }
details.task summary { min-height: 68px; padding: 16px 20px; cursor: pointer; list-style: none; display: flex; justify-content: space-between; align-items: center; gap: 14px; }
details.task summary::-webkit-details-marker { display: none; }
.task-title { font-weight: 800; font-size: 17px; overflow-wrap: anywhere; }
.task-meta { display: flex; flex-wrap: wrap; gap: 8px; }
.badge { display: inline-flex; align-items: center; min-height: 26px; padding: 4px 10px; border: 2px solid var(--c-black); font: 700 12px/1.2 var(--font-sans); background: var(--c-gray-light); }
.badge.level-LOW { background: var(--c-yellow); }
.badge.level-MEDIUM { background: var(--c-white); }
.badge.level-HIGH { background: var(--c-orange); }
.badge.level-UNKNOWN { background: var(--c-gray-light); color: #555; }
.task-body { border-top: 3px solid var(--c-black); padding: 20px; }
.task-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.machine, .human { padding: 16px; border: 3px solid var(--c-black); overflow-wrap: anywhere; }
.machine { background: var(--c-yellow); }
.machine h3, .human h3 { margin: 0 0 8px; font-size: 14px; }
.human { background: var(--c-black); color: var(--c-white); }
.task-reason { margin: 16px 0 0; font-size: 14px; overflow-wrap: anywhere; }
.raw-evidence { margin-top: 12px; padding: 12px 14px; border-left: 6px solid var(--c-orange); background: var(--c-gray-light); font-size: 13px; overflow-wrap: anywhere; }
.role-hit-chips { margin-top: 12px; display: flex; flex-wrap: wrap; gap: 8px; }
.role-hit-chips .badge { background: var(--c-white); font-family: var(--font-mono); }
.edge-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.edge { padding: 20px; background: var(--c-black); color: var(--c-yellow); border: 3px solid var(--c-black); box-shadow: 8px 8px 0 rgba(0,0,0,.15); font-size: 16px; font-weight: 650; overflow-wrap: anywhere; }
.action-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.action { padding: 22px; display: flex; flex-direction: column; background: var(--c-white); border: 3px solid var(--c-black); box-shadow: 8px 8px 0 rgba(0,0,0,.12); }
.action-label { font: 800 12px/1 var(--font-mono); letter-spacing: .12em; background: var(--c-black); color: var(--c-yellow); align-self: flex-start; padding: 6px 10px; }
.action h3 { margin: 14px 0 10px; font-size: 20px; line-height: 1.3; overflow-wrap: anywhere; }
.action p { margin: 0; font-size: 14px; overflow-wrap: anywhere; }
.action dl { margin: 14px 0 0; }
.action dt { margin-top: 10px; font: 800 12px/1.2 var(--font-mono); letter-spacing: .06em; }
.action dd { margin: 4px 0 0; font-size: 13px; overflow-wrap: anywhere; }
.share-copy { padding: 20px; margin-bottom: 18px; background: var(--c-white); border: 3px solid var(--c-black); font-size: 14px; }
.share-export-stage { width: min(560px, calc(100% - 40px)); margin: 0 auto 60px; }
#share-card-canvas { display: block; width: 100%; height: auto; background: var(--c-yellow); border: 3.5px solid var(--c-black); box-shadow: 10px 10px 0 rgba(0,0,0,.2); }
.download-button {
  width: 100%; min-height: 48px; margin-top: 14px; padding: 12px;
  background: var(--c-black); color: var(--c-yellow);
  border: 3px solid var(--c-black); box-shadow: 6px 6px 0 rgba(0,0,0,.25);
  font: 900 16px/1.3 var(--font-sans); cursor: pointer;
}
.download-button:focus-visible { outline: 3px solid var(--c-orange); outline-offset: 3px; }
.download-button[disabled] { background: var(--c-orange); color: var(--c-black); cursor: not-allowed; }
.method { padding: 24px; background: var(--c-white); border: 3px solid var(--c-black); box-shadow: 8px 8px 0 rgba(0,0,0,.12); }
.method p, .method li { font-size: 14px; }
.methodology-shell { width: min(1160px, calc(100% - 40px)); margin: 0 auto 70px; }
html.share-only, html.share-only body { width: 1080px; height: 1440px; overflow: hidden; background: var(--c-yellow); }
html.share-only .report-shell, html.share-only .methodology-shell { display: none; }
html.share-only .share-export-stage { width: 1080px; height: 1440px; margin: 0; }
html.share-only #share-card-canvas { width: 1080px; height: 1440px; border: 0; box-shadow: none; }
html.share-only .download-button { display: none; }
@media (max-width: 860px) {
  .hero-grid { grid-template-columns: 1fr; }
  .skill-grid { grid-template-columns: 1fr 1fr; }
  .action-grid { grid-template-columns: 1fr; }
  .edge-grid { grid-template-columns: 1fr; }
  .takeaway-row { grid-template-columns: 1fr; }
}
@media (max-width: 680px) {
  .report-shell, .methodology-shell { width: calc(100% - 24px); padding-top: 14px; }
  .poster-ticker { font-size: 11px; }
  .attitude-block { padding: 24px 20px; }
  .giant-index { font-size: 120px; }
  .giant-index.unknown { font-size: 56px; }
  .level-chip { font-size: 28px; }
  .character-title { font-size: 26px; }
  .snarky-banner { font-size: 19px; }
  .character-stage { padding: 14px 10px 12px; margin: 8px 0; border-radius: 12px; box-shadow: 4px 4px 0 var(--c-black); }
  .character-figure { width: min(220px, 100%); }
  .character-plinth { width: 64%; height: 16px; margin-top: -12px; }
  h2 { font-size: 22px; }
  details.task summary { align-items: flex-start; flex-direction: column; }
  .task-columns { grid-template-columns: 1fr; }
  .takeaway, .situation-paper { word-break: break-word; overflow-wrap: anywhere; }
  .situation-paper { padding: 18px; }
  section { margin-top: 42px; }
  .download-button { min-height: 44px; }
}
@media print {
  body { background: white; }
  .download-button { display: none; }
}
"""

CARD_SCRIPT = r"""
(() => {
  const cardData = __CARD_DATA__;
  const reportId = __REPORT_ID__;
  const roleCode = __ROLE_CODE__;
  const roleDefinition = __ROLE_DEFINITION__;
  const badge = __BADGE__;
  const assetMain = __ASSET_MAIN__;
  const assetShadow = __ASSET_SHADOW__;
  const assetBadge = __ASSET_BADGE__;
  const params = new URLSearchParams(window.location.search);
  if (params.get("share") === "1") document.documentElement.classList.add("share-only");

  const canvas = document.getElementById("share-card-canvas");
  const ctx = canvas.getContext("2d");
  const colors = { LOW: "#FF4A00", MEDIUM: "#FF4A00", HIGH: "#0D0D0D", UNKNOWN: "#555555" };
  const heavy = '"Arial Black", "Impact", "PingFang SC", sans-serif';
  const sans = '-apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif';
  const mono = '"SF Mono", "Consolas", "Monaco", monospace';
  const YELLOW = "#EBFB3B", BLACK = "#0D0D0D", ORANGE = "#FF4A00", WHITE = "#FFFFFF", GRAY = "#F4F4F0";

  function roundedRect(x, y, w, h, r, fill, stroke = null, strokeWidth = 3) {
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, r);
    ctx.fillStyle = fill;
    ctx.fill();
    if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = strokeWidth; ctx.stroke(); }
  }

  function wrapLines(text, maxWidth, maxLines = 3) {
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

  function drawWrapped(text, x, y, maxWidth, lineHeight, maxLines = 3) {
    const lines = wrapLines(text, maxWidth, maxLines);
    lines.forEach((line, index) => ctx.fillText(line, x, y + index * lineHeight));
    return y + lines.length * lineHeight;
  }

  function drawCard(image, badgeImage) {
    ctx.clearRect(0, 0, 1080, 1440);
    ctx.fillStyle = YELLOW; ctx.fillRect(0, 0, 1080, 1440);
    ctx.strokeStyle = BLACK; ctx.lineWidth = 14; ctx.strokeRect(20, 20, 1040, 1400);

    // 顶部公告条：左侧 mbai 品牌徽章（冻结露出位），右侧指标标题
    ctx.fillStyle = BLACK; ctx.fillRect(20, 20, 1040, 72);
    if (badgeImage) ctx.drawImage(badgeImage, 34, 28, 56, 56);
    ctx.fillStyle = YELLOW; ctx.font = `700 26px ${mono}`;
    ctx.fillText("AI IRREPLACEABILITY INDEX · 职业体检报告", 106, 68);
    ctx.textAlign = "right"; ctx.fillText("ROUND_HALF_UP_TO_5", 1024, 68); ctx.textAlign = "left";

    // 指数与角色立像（上 60%）
    ctx.fillStyle = BLACK; ctx.font = `700 24px ${mono}`;
    ctx.fillText(cardData.category, 56, 136);
    ctx.font = `800 28px ${sans}`;
    ctx.fillText("工作任务 AI 不可替代指数", 56, 186);
    const known = cardData.irreplaceability_index !== null && cardData.irreplaceability_index !== undefined;
    if (known) {
      ctx.font = `900 250px ${heavy}`;
      const numberText = String(cardData.irreplaceability_index);
      ctx.fillText(numberText, 52, 445);
      const numberWidth = ctx.measureText(numberText).width;
      ctx.font = `900 42px ${heavy}`;
      ctx.fillText("/ 100", 52 + numberWidth + 24, 445);
    } else {
      ctx.font = `900 110px ${heavy}`;
      ctx.fillText("暂无指数", 56, 400);
      ctx.font = `700 30px ${sans}`;
      ctx.fillStyle = "#444444";
      ctx.fillText("证据不够，不下结论", 60, 455);
    }
    const lv = cardData.irreplaceability_level;
    const levelText = { LOW: "LOW · 低不可替代", MEDIUM: "MEDIUM · 中不可替代", HIGH: "HIGH · 高不可替代", UNKNOWN: "UNKNOWN" }[lv] || "UNKNOWN";
    ctx.font = `900 34px ${heavy}`;
    const chipWidth = ctx.measureText(levelText).width + 48;
    // 颜色绑定随风险镜像：新 LOW/MEDIUM（可接管度高＝风险）＝警示橙，新 HIGH（安全）＝黑底黄字。
    const safe = lv === "HIGH";
    roundedRect(56, 490, chipWidth, 62, 0, lv === "UNKNOWN" ? GRAY : (safe ? BLACK : ORANGE), BLACK, 4);
    ctx.fillStyle = safe ? YELLOW : BLACK; ctx.fillText(levelText, 80, 533);

    if (image) {
      // 角色展示区物理隔离：纯白实体潮玩展示舱（Solid Specimen Capsule）
      roundedRect(546, 102, 474, 504, 18, BLACK, BLACK, 0);
      roundedRect(540, 96, 474, 504, 18, WHITE, BLACK, 5);

      // 舱内顶部工程标本条
      ctx.fillStyle = "#F4F4F0";
      ctx.fillRect(545, 101, 464, 36);
      ctx.fillStyle = BLACK;
      ctx.font = `700 15px ${mono}`;
      ctx.fillText(`SPECIMEN POD // ${badge} · ${roleCode}`, 562, 125);

      // 实体手办展台底座（在脚底先行绘制，避免遮挡手办脚部）
      ctx.fillStyle = BLACK;
      ctx.beginPath(); ctx.ellipse(777, 546, 175, 24, 0, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = "#2B2B2B";
      ctx.beginPath(); ctx.ellipse(777, 540, 145, 16, 0, 0, Math.PI * 2); ctx.fill();

      // 居中绘制实心潮玩立像
      ctx.drawImage(image, 557, 128, 440, 440);
    }

    // 角色名条（含定义句；神秘工时定义句即“证据不够，不下结论”）
    ctx.fillStyle = BLACK; ctx.fillRect(56, 640, 968, 128);
    ctx.fillStyle = WHITE; ctx.font = `900 52px ${sans}`;
    drawWrapped(cardData.role_name, 88, 700, 900, 60, 1);
    ctx.fillStyle = YELLOW; ctx.font = `600 26px ${sans}`;
    drawWrapped(roleDefinition, 88, 744, 830, 32, 1);

    // 嘴替横幅
    roundedRect(56, 800, 968, 150, 0, WHITE, BLACK, 6);
    ctx.fillStyle = BLACK; ctx.font = `900 44px ${heavy}`;
    drawWrapped(`“${cardData.snarky_quote}”`, 92, 866, 896, 56, 2);

    // 分工速览
    ctx.fillStyle = BLACK; ctx.font = `700 24px ${mono}`;
    ctx.fillText("分工速览 // WHO DOES WHAT", 56, 1002);
    cardData.task_highlights.slice(0, 2).forEach((item, index) => {
      const y = 1018 + index * 116;
      roundedRect(56, y, 968, 104, 0, WHITE, BLACK, 5);
      ctx.fillStyle = BLACK; ctx.font = `800 28px ${sans}`;
      ctx.fillText(item.task_name, 84, y + 38);
      ctx.font = `600 24px ${sans}`;
      ctx.fillStyle = "#333333";
      const aiLines = wrapLines(`AI：${item.ai_part}`, 430, 1);
      ctx.fillText(aiLines[0] || "", 84, y + 78);
      const humanLines = wrapLines(`人：${item.human_part}`, 400, 1);
      ctx.fillText(humanLines[0] || "", 560, y + 78);
    });

    // 7 天下一步
    roundedRect(56, 1256, 968, 118, 0, WHITE, BLACK, 5);
    ctx.fillStyle = ORANGE; ctx.fillRect(56, 1256, 18, 118);
    ctx.fillStyle = BLACK; ctx.font = `700 20px ${mono}`;
    ctx.fillText("7 天下一步 // NEXT MOVE", 96, 1288);
    ctx.font = `800 30px ${sans}`;
    drawWrapped(cardData.proof_7d, 96, 1326, 900, 36, 2);

    // 角落引导语与评级代码（必须完整落在画框内：底边框内缘约 y=1413，基线留足降部空间）
    ctx.fillStyle = BLACK; ctx.font = `700 24px ${sans}`;
    ctx.fillText("搜 欧八同学 生成自己的职业AI体检报告", 56, 1398);
    ctx.textAlign = "right"; ctx.font = `700 19px ${mono}`;
    ctx.fillText(`SPECIMEN CARD // ${badge} // ${roleCode}`, 1024, 1398);
    ctx.textAlign = "left";
  }

  function drawFailure(reason) {
    ctx.clearRect(0, 0, 1080, 1440);
    ctx.fillStyle = BLACK; ctx.fillRect(0, 0, 1080, 1440);
    ctx.fillStyle = ORANGE; ctx.font = `900 72px ${heavy}`;
    ctx.fillText("素材加载失败", 80, 640);
    ctx.fillStyle = YELLOW; ctx.font = `700 34px ${sans}`;
    drawWrapped(`角色素材解码失败，已显式中止导出：${reason}`, 80, 740, 900, 48, 3);
    ctx.font = `700 26px ${mono}`;
    ctx.fillText("EXPORT ABORTED // NO SILENT MISSING-CHARACTER CARD", 80, 900);
  }

  function loadImage(dataUri) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => img.decode().then(() => resolve(img)).catch(reject);
      img.onerror = () => reject(new Error("image decode failed"));
      img.src = dataUri;
    });
  }

  function updateLayoutProbe() {
    const root = document.documentElement;
    root.setAttribute("data-horizontal-overflow", String(root.scrollWidth > window.innerWidth));
    root.setAttribute("data-viewport-width", String(window.innerWidth));
    root.setAttribute("data-scroll-width", String(root.scrollWidth));
  }

  async function boot() {
    try {
      if (document.fonts && document.fonts.ready) await document.fonts.ready;
      const [image, badgeImage] = await Promise.all([loadImage(assetMain), loadImage(assetBadge)]);
      drawCard(image, badgeImage);
      window.__CARD_READY__ = true;
      window.__CARD_ERROR__ = null;
    } catch (error) {
      drawFailure(error && error.message ? error.message : String(error));
      window.__CARD_READY__ = false;
      window.__CARD_ERROR__ = String(error);
      const button = document.getElementById("download-card");
      if (button) { button.disabled = true; button.textContent = "素材加载失败，导出已中止"; }
    }
    updateLayoutProbe();
  }

  window.addEventListener("resize", updateLayoutProbe);
  document.getElementById("download-card").addEventListener("click", () => {
    if (window.__CARD_ERROR__) return;
    canvas.toBlob((blob) => {
      if (!blob || window.__CARD_ERROR__) return;
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `${reportId}-share-card.png`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(link.href), 1000);
    }, "image/png");
  });

  boot();
})();
"""


def _skill_card(name: str, item: dict[str, Any]) -> str:
    known = bool(item.get("is_known"))
    score = item.get("score") if known else None
    value = f"{score}" if score is not None else "未知"
    width = max(0, min(100, int(score or 0)))
    return f"""
      <article class="skill-card">
        <h3>{_e(SKILL_LABELS[name])}</h3>
        <div class="skill-score">{_e(value)}{f'<small> / 100</small>' if score is not None else ''}</div>
        <div class="skill-meter" aria-hidden="true"><span style="width:{width}%"></span></div>
        <p class="skill-evidence">{_e(item.get('evidence') or '简历未提及')}</p>
      </article>"""


def _task_card(task: dict[str, Any]) -> str:
    level = task["exposure_level"]
    time_label = f"时间占比 {_e(task['time_share_percent'])}%" if task.get("time_share_percent") is not None else "等权"
    hit_codes = task.get("role_codes") or []
    chips = "".join(f'<span class="badge">{_e(ROLE_BY_CODE[code]["name"])}</span>' for code in hit_codes)
    chips_block = f'<div class="role-hit-chips"><span class="badge">角色命中</span>{chips}</div>' if chips else ""
    return f"""
      <details class="task" open>
        <summary>
          <span class="task-title">{_e(task['task_name'])}</span>
          <span class="task-meta">
            <span class="badge level-{level.lower()}">{_e(TASK_LEVEL_LABELS[level])}</span>
            <span class="badge">{time_label}</span>
            <span class="badge">证据 {_e(task['confidence'])}</span>
          </span>
        </summary>
        <div class="task-body">
          <div class="task-columns">
            <div class="machine"><h3>AI 能接手</h3><div>{_e(task['ai_can_do'])}</div></div>
            <div class="human"><h3>你来把关</h3><div>{_e(task['human_must_do'])}</div></div>
          </div>
          <p class="task-reason"><strong>判断理由：</strong>{_e(task['reason'])}</p>
          <div class="raw-evidence"><strong>证据原文：</strong>{_e(task['evidence'])}</div>
          {chips_block}
        </div>
      </details>"""


def _action_card(kind: str, action: dict[str, Any]) -> str:
    return f"""
      <article class="action">
        <div class="action-label">{_e(ACTION_LABELS[kind])}</div>
        <h3>{_e(action['title'])}</h3>
        <p>{_e(action['action'])}</p>
        <dl>
          <dt>交付物</dt><dd>{_e(action['deliverable'])}</dd>
          <dt>算完成</dt><dd>{_e(action['acceptance_criteria'])}</dd>
          <dt>人工检查点</dt><dd>{_e(action['human_checkpoint'])}</dd>
          <dt>经历依据</dt><dd>{_e(action['grounded_evidence'])}</dd>
        </dl>
      </article>"""


def render_report(report: dict[str, Any]) -> str:
    """Render exactly what final JSON says; scoring and role matching belong upstream."""
    metadata = report["report_metadata"]
    profile = report["profile"]
    role = profile["role"]
    metrics = report["metrics"]
    index = metrics["irreplaceability_index"]
    level = metrics["irreplaceability_level"]
    assets = _role_assets(report)

    index_attr = "unknown" if index is None else str(index)
    giant = "暂无指数" if index is None else f"{index}"
    giant_class = "unknown" if index is None else ""
    situation = profile.get("situation_paragraph") or ""
    index_note = profile.get("index_note") or ""

    evaluable = [task for task in report["tasks"] if task["exposure_level"] != "UNKNOWN"]
    affected = sorted(
        evaluable,
        key=lambda task: (task.get("score", -1), task.get("time_share_percent") or 0),
        reverse=True,
    )[:2]
    affected_text = "；".join(f"{item['task_name']}（{TASK_LEVEL_LABELS[item['exposure_level']]}）" for item in affected) or "现有证据不足，暂不判断受影响任务。"
    edge_text = report["human_edge"][0]["summary"]

    tags = "".join(f'<span class="badge">{_e(tag)}</span>' for tag in role["tags"])
    skills = "".join(_skill_card(name, report["skill_panel"][name]) for name in SKILL_LABELS)
    tasks = "".join(_task_card(task) for task in report["tasks"])
    edges = "".join(f'<article class="edge">{_e(point["summary"])}</article>' for point in report["human_edge"])
    actions = "".join(_action_card(kind, report["action_plan"][kind]) for kind in ACTION_LABELS)
    sources = "".join(
        f'<li><strong>{_e(source["organization"])}</strong>：<a href="{_e(source["url"])}" target="_blank" rel="noreferrer">{_e(source["title"])}</a>（发布 {_e(source["publication_date"])}；访问 {_e(source["accessed_at"])}）。{_e(source["boundary"])}</li>'
        for source in report["methodology"]["sources"]
    )

    card_script = (
        CARD_SCRIPT.replace("__CARD_DATA__", _json_for_script(report["share_card"]))
        .replace("__REPORT_ID__", _json_for_script(metadata["report_id"]))
        .replace("__ROLE_CODE__", _json_for_script(assets["code"]))
        .replace("__ROLE_DEFINITION__", _json_for_script(assets["definition"]))
        .replace("__BADGE__", _json_for_script(assets["badge"]))
        .replace("__ASSET_BADGE__", _json_for_script(assets["brand_badge"]))
        .replace("__ASSET_MAIN__", _json_for_script(assets["main"]))
        .replace("__ASSET_SHADOW__", _json_for_script(assets["shadow"]))
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="color-scheme" content="light">
  <title>{_e(role['name'])}｜工作任务 AI 不可替代指数</title>
  <style>{STYLE}</style>
</head>
<body>
  <main class="report-shell">
    <div class="poster-ticker">
      <span class="ticker-brand"><img class="ticker-badge" src="{assets['brand_badge']}" alt="mbai 徽章">mbai</span>
      <span>WORK TASK // AI IRREPLACEABILITY INDEX</span>
      <span class="ticker-secondary">RULE v{_e(report['rule_version'])} · {_e(assets['badge'])}</span>
      <span class="ticker-secondary">不可替代指数量的也是任务，不是人</span>
    </div>
    <section id="hero">
      <div class="hero-grid">
        <div class="attitude-block">
          <div class="attitude-index-row" data-irreplaceability-index="{_e(index_attr)}">
            <div class="giant-index {giant_class}" aria-label="工作任务 AI 不可替代指数 {_e(index_attr)}">{giant}</div>
            <div>
              <span class="level-chip level-{level.lower()}">{_e(level)} · {_e(SUMMARY_LEVEL_LABELS[level])}</span>
              <p class="index-caption">{_e(index_note)}</p>
            </div>
          </div>
          <h1 class="character-title">{_e(role['name'])}</h1>
          <p class="character-definition">{_e(assets['definition'])}</p>
          <div class="snarky-banner">{_e(role['snarky_quote'])}</div>
        </div>
        <div class="stage-block">
          <div class="specimen-capsule">
            <span>{_e(assets['badge'])}</span>
            <span>{_e(assets['code'])}</span>
          </div>
          <div class="character-stage">
            <img class="character-figure" src="{assets['main']}" alt="{_e(role['name'])} 立像">
            <div class="character-plinth" aria-hidden="true"></div>
          </div>
          <div class="stage-nameplate">
            <strong>{_e(role['name'])}</strong>
            {_e(assets['definition'])}
            <div class="task-meta" style="margin-top:10px">{tags}</div>
          </div>
        </div>
      </div>
      <div class="situation-paper">
        <div class="section-no">01 // SITUATION</div>
        <p>{_e(situation)}</p>
      </div>
      <div class="takeaway-row">
        <div class="takeaway"><strong>最受影响任务</strong><p>{_e(affected_text)}</p></div>
        <div class="takeaway"><strong>你仍然值钱的地方</strong><p>{_e(edge_text)}</p></div>
      </div>
    </section>

    <section id="skill-panel">
      <div class="section-head"><div><span class="section-no">02 // ATTRIBUTES</span><h2>四维任务证据</h2></div><p class="section-note">四项只显示简历与补问中实际出现的证据；未知不是零分。</p></div>
      <div class="skill-grid">{skills}</div>
    </section>

    <section id="task-breakdown">
      <div class="section-head"><div><span class="section-no">03 // TASK ANATOMY</span><h2>哪些交给 AI、哪些还得我管</h2></div><p class="section-note">每项任务展开可见 AI 能接手的部分、你来把关的部分与原文证据。</p></div>
      <div class="task-list">{tasks}</div>
    </section>

    <section id="human-edge">
      <div class="section-head"><div><span class="section-no">04 // HUMAN EDGE</span><h2>AI 介入后，你仍然值钱的地方</h2></div><p class="section-note">值得保留和强化的具体贡献，全部来自任务证据。</p></div>
      <div class="edge-grid">{edges}</div>
    </section>

    <section id="action-plan">
      <div class="section-head"><div><span class="section-no">05 // NEXT MOVES</span><h2>接下来做什么：三个行动</h2></div><p class="section-note">全部来自你的任务证据，7 天内可启动，完成标准可客观检验。</p></div>
      <div class="action-grid">{actions}</div>
    </section>

    <section id="share-export">
      <div class="section-head"><div><span class="section-no">06 // SHARE</span><h2>脱敏分享卡</h2></div><p class="section-note">PNG 只使用独立的脱敏字段，不包含姓名、联系方式、公司、学校、客户、项目名或完整简历。</p></div>
      <div class="share-copy">下方卡片由浏览器原生 Canvas 生成，角色素材以 data URI 内嵌。点击按钮会在本机导出严格 1080 × 1440 的 PNG，无需联网；素材加载失败时导出会显式中止。</div>
    </section>
  </main>

  <div class="share-export-stage">
    <canvas id="share-card-canvas" width="1080" height="1440" aria-label="脱敏职业诊断分享卡"></canvas>
    <button id="download-card" class="download-button" type="button">保存 1080 × 1440 脱敏卡</button>
  </div>

  <footer id="methodology" class="methodology-shell">
    <div class="method">
      <span class="section-no">07 // METHOD &amp; BOUNDARY</span><h2>方法与边界</h2>
      <p><strong>{_e(report['methodology']['custom_rules_disclaimer'])}</strong></p>
      <ul>{sources}</ul>
      <p class="brand-lockup">{BRAND_LOCKUP}</p>
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
