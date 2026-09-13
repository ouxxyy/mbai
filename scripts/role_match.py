"""Deterministic role matching for the frozen 12-role system (R1–R5).

规则来源：docs/SCORING_RULES.md §6（内容基线冻结版，2026-09-13）。
- R1 命中谓词：信号约束全部满足，且任务动词命中该角色动词表、对象命中该角色对象表，
  三者同时成立才算命中；动词、对象从任务原文证据判定，不从岗位名称判定。
  UNKNOWN 任务不参与命中；零命中的可判断任务记为“角色不可判”。
- R2 主角色 = 覆盖权重最大的角色；单任务权重 w = 时间占比，缺失时按 1 计（EQUAL_FALLBACK）。
- R3 并列固定消解：按表序 1–12 取先者。
- R4 两道门槛独立：指数门槛 = 暴露可判 ×2 ≥ 全部；主角色门槛 = 角色可判 ×2 ≥ 全部。
- R5 角色与指数解耦：本引擎不读取任何暴露等级或分数。

动词/对象表是冻结命中表（动词＋对象）的工程同义词扩展：只增加同一动作/对象的
常见中文写法，不跨角色挪用边界词；表本身是常量，测试逐角色锚定。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any


ROLE_SIGNAL_KEYS = (
    "judgment",
    "coordination",
    "physical_presence",
    "accountability",
    "repeatability",
    "digital_input_output",
)

# 每个信号约束为 (min, max)，未列出的信号默认 (0, 2)；
# "or_signals" 表示括号内任一信号达到即视为满足（守门兽：判2 或 责2）。
ROLES: list[dict[str, Any]] = [
    {
        "code": "TABLE_WORKER",
        "order": 1,
        "name": "搬表工",
        "definition": "你把数据从 A 搬到 B，顺便当格式转换器。",
        "asset": "01_table_worker.webp",
        "badge": "TW-01",
        "tags": ["表格搬运", "格式转换"],
        "verbs": ["导出", "导入", "合并", "录入", "填报", "填写", "填入", "汇总", "搬运", "转录", "更新表"],
        "objects": ["数据", "表格", "报表", "周报", "模板", "表"],
        "signals": {"repeatability": (2, 2), "digital_input_output": (2, 2), "judgment": (0, 1), "coordination": (0, 1)},
    },
    {
        "code": "INSPECTOR_WORKER",
        "order": 2,
        "name": "巡检工",
        "definition": "按清单跑流程，链接、字段、库存，一个都不能错。",
        "asset": "02_inspector_worker.webp",
        "badge": "TW-02",
        "tags": ["流程巡检", "按清单执行"],
        "verbs": ["配置", "发布", "检查", "巡检", "核对字段", "核验"],
        "objects": ["后台", "清单", "字段", "链接", "库存", "排期", "模板"],
        "signals": {"repeatability": (2, 2), "digital_input_output": (1, 2), "judgment": (0, 1)},
    },
    {
        "code": "PROOFREADER_WORKER",
        "order": 3,
        "name": "校稿工",
        "definition": "同一句话要说给不同的人听，你保证它每次都说得对。",
        "asset": "03_proofreader_worker.webp",
        "badge": "TW-03",
        "tags": ["口径校准", "事实把关"],
        "verbs": ["审核", "校对", "查核", "核查", "统一口径", "校准", "把关"],
        "objects": ["文案", "风格", "标准", "口径", "语气", "表述", "事实", "删改"],
        "signals": {"judgment": (1, 2), "digital_input_output": (2, 2), "accountability": (1, 2)},
    },
    {
        "code": "ASSEMBLY_WORKER",
        "order": 4,
        "name": "拼装工",
        "definition": "素材从四面八方来，成品从你手里出去。",
        "asset": "04_assembly_worker.webp",
        "badge": "TW-04",
        "tags": ["素材组装", "多版本产出"],
        "verbs": ["整理", "组装", "排版", "拼装", "撰写", "写作", "写稿", "剪辑", "生成内容"],
        "objects": ["素材", "内容", "版本", "多版本", "文章", "初稿", "稿件", "专题"],
        "signals": {"repeatability": (1, 2), "digital_input_output": (2, 2), "judgment": (0, 1)},
    },
    {
        "code": "ROOTCAUSE_WORKER",
        "order": 5,
        "name": "追因工",
        "definition": "报表异常只是表象，顺着链路定位根因的是你。",
        "asset": "05_rootcause_worker.webp",
        "badge": "TW-05",
        "tags": ["数据追因", "根因定位"],
        "verbs": ["分析", "定位", "排查", "验证", "归因", "追因", "诊断", "查明"],
        "objects": ["异常", "波动", "原因", "根因"],
        "signals": {"judgment": (1, 2), "coordination": (1, 2)},
    },
    {
        "code": "GATEKEEPER_WORKER",
        "order": 6,
        "name": "守门工",
        "definition": "拦截隐患于发生之前，把关质量于交付之初。",
        "asset": "06_gatekeeper_worker.webp",
        "badge": "TW-06",
        "tags": ["系统守门", "质量把关"],
        "verbs": ["审查", "拦截", "批准", "审批", "测试", "把关", "签字", "边界检查", "评审"],
        "objects": ["权限", "边界", "质量", "上线", "合并"],
        "signals": {},
        "or_signals": [("judgment", 2), ("accountability", 2)],
    },
    {
        "code": "TRANSLATOR_WORKER",
        "order": 7,
        "name": "翻译工",
        "definition": "两边都说中文，但只有你能对上话。",
        "asset": "07_translator_worker.webp",
        "badge": "TW-07",
        "tags": ["跨组翻译", "信息对齐"],
        "verbs": ["协调", "对齐", "转述", "同步", "协商", "拉齐", "传达"],
        "objects": ["需求", "信息", "团队误解", "误解", "分歧", "冲突", "意见"],
        "signals": {"coordination": (2, 2)},
    },
    {
        "code": "DECONSTRUCTOR_WORKER",
        "order": 8,
        "name": "拆解工",
        "definition": "别人给想法，你给可执行的清单。",
        "asset": "08_deconstructor_worker.webp",
        "badge": "TW-08",
        "tags": ["需求拆解", "模糊转清单"],
        "verbs": ["拆解", "澄清", "细化", "转化", "梳理需求"],
        "objects": ["模糊诉求", "一句话需求", "模糊需求", "诉求", "想法"],
        "signals": {"judgment": (1, 2), "digital_input_output": (1, 2)},
    },
    {
        "code": "PROGRESS_WORKER",
        "order": 9,
        "name": "催办工",
        "definition": "所有人的延期，都会先出现在你的表格里。",
        "asset": "09_progress_worker.webp",
        "badge": "TW-09",
        "tags": ["进度追踪", "催办推动"],
        "verbs": ["排期", "跟进", "催办", "更新", "汇总", "推动"],
        "objects": ["进度", "依赖", "里程碑", "延期"],
        "signals": {"coordination": (1, 2), "repeatability": (1, 2)},
    },
    {
        "code": "MINESWEEPER_WORKER",
        "order": 10,
        "name": "排雷工",
        "definition": "项目炸之前，只有你天天问“万一呢”。",
        "asset": "10_minesweeper_worker.webp",
        "badge": "TW-10",
        "tags": ["项目排雷", "风险兜底"],
        "verbs": ["识别风险", "评估", "应对", "兜底", "处置", "风险预警"],
        "objects": ["风险", "故障", "结果", "隐患"],
        "signals": {"accountability": (2, 2), "judgment": (1, 2)},
    },
    {
        "code": "SOLVER_WORKER",
        "order": 11,
        "name": "解题工",
        "definition": "客户的问题没有标准答案，你现场拼一个。",
        "asset": "11_solver_worker.webp",
        "badge": "TW-11",
        "tags": ["客户解题", "例外处理"],
        "verbs": ["理解场景", "处理例外", "解答", "解决客户", "答疑"],
        "objects": ["客户", "例外"],
        "signals": {"judgment": (1, 2), "coordination": (1, 2)},
    },
    {
        "code": "ONSCENE_WORKER",
        "order": 12,
        "name": "应变工",
        "definition": "消息传到你这儿已经晚了十分钟，好在你人就在那儿。",
        "asset": "12_onscene_worker.webp",
        "badge": "TW-12",
        "tags": ["现场应变", "即时处置"],
        "verbs": ["到场", "到现场", "即时处置", "现场协调", "现场处置", "现场应对"],
        "objects": ["现场", "突发", "设备"],
        "signals": {"physical_presence": (1, 2), "coordination": (1, 2)},
    },
]

SHADOW_WORKER = {
    "code": "SHADOW_WORKER",
    "order": 0,
    "name": "神秘工 · 待解锁",
    "definition": "证据不够，不下结论。",
    "asset": "00_shadow_worker.webp",
    "badge": "TW-00",
    "tags": ["证据待补充"],
}
# 3.x 时代别名（仅迁移与文档引用；判定与渲染一律使用 SHADOW_WORKER）。
SHADOW_BEAST = SHADOW_WORKER

ROLE_BY_CODE = {role["code"]: role for role in ROLES}
ROLE_NAMES = {role["code"]: role["name"] for role in ROLES}
ROLE_NAMES[SHADOW_BEAST["code"]] = SHADOW_BEAST["name"]
ROLE_CODES = tuple(ROLE_NAMES)

# 旧六角色 → 新 12 类迁移映射（冻结版②迁移表；实际归属由引擎按任务证据重判）。
LEGACY_ROLE_MIGRATION = {
    "FLOW_ORCHESTRATOR": ["TABLE_WORKER", "INSPECTOR_WORKER", "PROGRESS_WORKER"],
    "CONTENT_CALIBRATOR": ["PROOFREADER_WORKER", "ASSEMBLY_WORKER"],
    "SYSTEM_BOUNDARY_GUARD": ["GATEKEEPER_WORKER"],
    "COORDINATION_TRANSLATOR": ["TRANSLATOR_WORKER", "DECONSTRUCTOR_WORKER", "SOLVER_WORKER"],
    "PROJECT_RISK_NAVIGATOR": ["MINESWEEPER_WORKER", "ONSCENE_WORKER"],
    "LOCKED_ROLE": ["SHADOW_WORKER"],
}
LEGACY_ROLE_NAMES = {
    "FLOW_ORCHESTRATOR": "流程编排员",
    "CONTENT_CALIBRATOR": "内容校准师",
    "SYSTEM_BOUNDARY_GUARD": "系统边界守门人",
    "COORDINATION_TRANSLATOR": "多方协同译码员",
    "PROJECT_RISK_NAVIGATOR": "项目风险领航员",
    "LOCKED_ROLE": "待解锁职业角色",
    # 2.0.0/3.0.0 兽时代（4.0.0 起废弃，仅迁移映射与历史工件解读）
    "TABLE_GOBLIN": "搬表兽 · 表格搬运官",
    "INSPECTOR_BOT": "巡检兽 · 流程巡航员",
    "PROOFREADER_OWL": "校稿兽 · 口径校准员",
    "ASSEMBLY_CRANE": "拼装兽 · 素材组装手",
    "ROOTCAUSE_HOUND": "追因兽 · 归因探查员",
    "GATEKEEPER_BEAR": "守门兽 · 上线守门员",
    "TRANSLATOR_FOX": "翻译兽 · 信息对齐官",
    "DECONSTRUCTOR_BEAVER": "拆解兽 · 清单拆解手",
    "PROGRESS_HERDER": "催办兽 · 进度推土机",
    "MINESWEEPER_MOLE": "排雷兽 · 风险预警员",
    "SOLVER_OTTER": "解题兽 · 现场解题手",
    "ONSCENE_CHAMELEON": "应变兽 · 实时响应员",
    "SHADOW_BEAST": "影子兽 · 待解锁工种",
}

# 4.0.0 机械改名映射：3.x 兽 code → 4.0.0 工 code（一一对应，语义零变化）。
BEAST_TO_WORKER = {
    "TABLE_GOBLIN": "TABLE_WORKER",
    "INSPECTOR_BOT": "INSPECTOR_WORKER",
    "PROOFREADER_OWL": "PROOFREADER_WORKER",
    "ASSEMBLY_CRANE": "ASSEMBLY_WORKER",
    "ROOTCAUSE_HOUND": "ROOTCAUSE_WORKER",
    "GATEKEEPER_BEAR": "GATEKEEPER_WORKER",
    "TRANSLATOR_FOX": "TRANSLATOR_WORKER",
    "DECONSTRUCTOR_BEAVER": "DECONSTRUCTOR_WORKER",
    "PROGRESS_HERDER": "PROGRESS_WORKER",
    "MINESWEEPER_MOLE": "MINESWEEPER_WORKER",
    "SOLVER_OTTER": "SOLVER_WORKER",
    "ONSCENE_CHAMELEON": "ONSCENE_WORKER",
    "SHADOW_BEAST": "SHADOW_WORKER",
}


def _task_text(task: dict[str, Any]) -> str:
    """R1：动词、对象从任务原文证据判定（任务名＋证据原文），不从岗位名称判定。"""
    return f"{task.get('task_name', '')}\n{task.get('evidence', '')}"


def _signals_ok(task: dict[str, Any], role: dict[str, Any]) -> bool:
    signals = task.get("signals") or {}
    if not isinstance(signals, dict):
        return False
    for key, (low, high) in role.get("signals", {}).items():
        value = signals.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
            return False
    alternatives = role.get("or_signals")
    if alternatives:
        signals_ok_any = False
        for key, required in alternatives:
            value = signals.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and value == required:
                signals_ok_any = True
                break
        if not signals_ok_any:
            return False
    return True


def match_task_roles(task: dict[str, Any]) -> list[str]:
    """R1：返回任务命中的全部角色 code（按表序）；UNKNOWN 任务一律返回 []。"""
    if task.get("exposure_level") == "UNKNOWN":
        return []
    text = _task_text(task)
    hits = []
    for role in ROLES:
        verb_hit = any(verb in text for verb in role["verbs"])
        object_hit = any(obj in text for obj in role["objects"])
        if verb_hit and object_hit and _signals_ok(task, role):
            hits.append(role["code"])
    return hits


def analyze_roles(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """R1–R4：任务级角色命中、覆盖权重、主角色与主角色门槛。

    返回：
    - task_roles: 与 tasks 等长的命中 code 列表（UNKNOWN/零命中为 []）
    - task_weights: 与 tasks 等长的覆盖权重（时间占比，缺失按 1；不可判任务为 None）
    - coverage: 各角色覆盖权重（全部缺失时即命中条数）
    - main_role: 主角色 code；主角色门槛未过时为 None
    - role_evaluable: 至少命中一个角色的任务条数
    - is_role_sufficient: 角色可判 × 2 ≥ 全部任务数
    """
    task_roles: list[list[str]] = []
    task_weights: list[float | int | None] = []
    coverage: dict[str, Decimal] = {}

    for task in tasks:
        roles = match_task_roles(task)
        task_roles.append(roles)
        if not roles:
            task_weights.append(None)
            continue
        share = task.get("time_share_percent")
        weight = Decimal(str(share)) if share is not None else Decimal("1")
        task_weights.append(float(weight) if weight % 1 else int(weight))
        for code in roles:
            coverage[code] = coverage.get(code, Decimal("0")) + weight

    total = len(tasks)
    role_evaluable = sum(1 for roles in task_roles if roles)
    is_role_sufficient = total > 0 and role_evaluable * 2 >= total

    main_role = None
    if is_role_sufficient and coverage:
        # R2 同一公式：占比缺失按 1 计，因此全部缺失时覆盖权重自然退化为命中条数。
        # R3 并列消解：权重相同时取表序在前者。
        main_role = max(
            coverage.items(),
            key=lambda item: (item[1], -ROLE_BY_CODE[item[0]]["order"]),
        )[0]

    return {
        "task_roles": task_roles,
        "task_weights": task_weights,
        "coverage": {code: float(value) for code, value in coverage.items()},
        "role_evaluable": role_evaluable,
        "is_role_sufficient": is_role_sufficient,
        "main_role": main_role,
    }


def main_role_source_task_ids(tasks: list[dict[str, Any]], main_role: str) -> list[str]:
    return [task["task_id"] for task in tasks if main_role in match_task_roles(task)]
