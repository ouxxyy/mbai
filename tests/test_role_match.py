"""Role matching engine tests: 12 fictional role cases + R1–R5 semantics."""

import unittest
from copy import deepcopy

from scripts.finalize_report import finalize_report
from scripts.role_match import ROLES, ROLE_BY_CODE, analyze_roles, match_task_roles
from scripts.validate_report import assert_valid_report


def _signals(judgment=0, coordination=0, physical=0, accountability=0, repeatability=0, digital=0):
    return {
        "judgment": judgment,
        "coordination": coordination,
        "physical_presence": physical,
        "accountability": accountability,
        "repeatability": repeatability,
        "digital_input_output": digital,
    }


def _task(task_id, name, evidence, level, share, signals, ai="AI 完成机械部分。", human="你来把关关键判断。"):
    return {
        "task_id": task_id,
        "task_name": name,
        "time_share_percent": share,
        "exposure_level": level,
        "ai_can_do": ai,
        "human_must_do": human,
        "evidence": evidence,
        "reason": "虚构验收案例：固定输入输出与责任边界清晰。",
        "confidence": "HIGH",
        "signals": signals,
    }


NEUTRAL_TASK = _task(
    "task-weekly-sync",
    "参加部门例会",
    "每周参加部门例会，口头汇报个人工作近况。",
    "LOW",
    30,
    _signals(1, 1, 0, 1, 1, 1),
)

# 12 类角色各一条虚构命中任务（动词＋对象＋信号均落表内，权重 70% 保证主角色）。
ROLE_TASKS = {
    "TABLE_GOBLIN": _task("task-role", "多源数据周报搬运", "从五个互不相通的系统导出运营数据，清洗合并后录入固定周报模板。", "HIGH", 70, _signals(1, 1, 0, 1, 2, 2)),
    "INSPECTOR_BOT": _task("task-role", "后台流程巡检", "按发布清单在后台配置活动，逐项检查链接与库存字段。", "HIGH", 70, _signals(0, 0, 0, 1, 2, 2)),
    "PROOFREADER_OWL": _task("task-role", "对外口径校准", "审核对外文案，统一品牌口径并对事实表述把关。", "MEDIUM", 70, _signals(2, 0, 0, 2, 1, 2)),
    "ASSEMBLY_CRANE": _task("task-role", "多版本内容组装", "把四方收集的素材整理排版，组装成多版本内容专题。", "HIGH", 70, _signals(1, 0, 0, 1, 2, 2)),
    "ROOTCAUSE_HOUND": _task("task-role", "数据异常追因", "排查数据异常，沿链路定位波动原因并验证候选根因。", "MEDIUM", 70, _signals(2, 2, 0, 1, 0, 2)),
    "GATEKEEPER_BEAR": _task("task-role", "上线质量守门", "审查上线权限与系统边界，测试通过后才批准发布。", "MEDIUM", 70, _signals(2, 1, 0, 2, 1, 2)),
    "TRANSLATOR_FOX": _task("task-role", "跨组信息对齐", "协调两个团队的需求，反复对齐信息以消除团队误解。", "MEDIUM", 70, _signals(1, 2, 0, 1, 1, 2)),
    "DECONSTRUCTOR_BEAVER": _task("task-role", "模糊需求拆解", "把一句话模糊诉求澄清细化，转化成可执行要求。", "MEDIUM", 70, _signals(2, 0, 0, 1, 1, 2)),
    "PROGRESS_HERDER": _task("task-role", "项目进度催办", "跟进项目排期，对延期依赖逐项催办并更新里程碑。", "MEDIUM", 70, _signals(1, 2, 0, 1, 2, 1)),
    "MINESWEEPER_MOLE": _task("task-role", "项目风险兜底", "识别上线风险，评估故障影响并对结果负责兜底。", "LOW", 70, _signals(2, 1, 0, 2, 0, 1)),
    "SOLVER_OTTER": _task("task-role", "客户例外处理", "理解客户场景，处理例外工单并解答疑难问题。", "MEDIUM", 70, _signals(2, 2, 0, 1, 0, 2)),
    "ONSCENE_CHAMELEON": _task("task-role", "现场突发响应", "设备突发告警时第一时间到场，现场协调抢修与恢复。", "LOW", 70, _signals(1, 2, 2, 2, 0, 1)),
}


def _role_draft(role_code, *, second_level="LOW", second_share=30):
    """两条任务的虚构草稿：目标角色任务 + 中性例会任务。"""
    role_task = deepcopy(ROLE_TASKS[role_code])
    second = deepcopy(NEUTRAL_TASK)
    second["exposure_level"] = second_level
    second["time_share_percent"] = second_share
    return {
        "schema_version": "2.0.0",
        "rule_version": "2.0.0",
        "report_metadata": {
            "report_id": f"role-case-{role_code.lower()}",
            "generated_at": "2026-09-11T20:00:00+08:00",
            "confidence_level": "HIGH",
            "confidence_reason": "虚构验收案例，任务边界清晰。",
            "questions_asked": [],
            "questions_skipped": False,
        },
        "source": {
            "input_type": "TEXT",
            "input_name": "fictional.txt",
            "privacy_entities": [],
            "extraction_status": "OK",
        },
        "profile": {
            "sanitized_category": "虚构 / 角色验收",
            "situation_paragraph": "虚构案例：把一个角色的典型工作日拆成两条任务。",
            "index_note": "替代指数量的是任务，不是人。",
            "role": {
                "code": role_code,
                "name": ROLE_BY_CODE[role_code]["name"],
                "tags": ROLE_BY_CODE[role_code]["tags"],
                "source_task_ids": ["task-role"],
                "snarky_quote": "虚构嘴替句，仅用于角色验收。",
            },
        },
        "skill_panel": {
            key: {"score": None, "evidence": "虚构案例未展开", "is_known": False, "source_task_ids": []}
            for key in ("execution", "discretion", "coordination", "accountability")
        },
        "tasks": [role_task, second],
        "human_edge": [{"summary": "虚构边界：判断与责任留在人。", "source_task_ids": ["task-role"]}],
        "action_plan": {
            "hand_to_ai": {
                "title": "交给 AI 的虚构动作",
                "action": "把机械部分脚本化。",
                "deliverable": "一份脚本",
                "acceptance_criteria": "7 天内跑通一次。",
                "human_checkpoint": "发布前人工复核。",
                "grounded_evidence": "任务输入输出固定。",
                "source_task_ids": ["task-role"],
            },
            "level_up": {
                "title": "强化虚构判断力",
                "action": "记录三次判断过程。",
                "deliverable": "三张判断卡",
                "acceptance_criteria": "每张含两个备选。",
                "human_checkpoint": "区分事实与推测。",
                "grounded_evidence": "任务含判断责任。",
                "source_task_ids": ["task-role"],
            },
            "proof_7d": {
                "title": "七天虚构作品",
                "action": "做一份前后对照。",
                "deliverable": "一页说明",
                "acceptance_criteria": "7 天内完成并含三个核验点。",
                "human_checkpoint": "数据全虚构。",
                "grounded_evidence": "源于目标任务的固定流程。",
                "source_task_ids": ["task-role"],
            },
        },
        "share_card": {
            "category": "虚构 / 角色验收",
            "role_name": ROLE_BY_CODE[role_code]["name"],
            "role_tags": ROLE_BY_CODE[role_code]["tags"],
            "confidence_label": "证据置信度：高",
            "irreplaceability_index": None,
            "irreplaceability_level": "UNKNOWN",
            "snarky_quote": "虚构嘴替句，仅用于角色验收。",
            "task_highlights": [
                {"task_name": "目标任务", "ai_part": "机械部分", "human_part": "关键判断"}
            ],
            "proof_7d": "七天虚构作品；7 天内完成并含三个核验点。",
            "disclaimer": "本卡反映工作任务与 AI 能力的重合度，不是个人失业概率。",
        },
    }


class TwelveRoleCasesTest(unittest.TestCase):
    def test_every_role_has_a_valid_fictional_case_landing_on_itself(self):
        for role in ROLES:
            with self.subTest(role=role["code"]):
                report = finalize_report(_role_draft(role["code"]))

                assert_valid_report(report)
                self.assertEqual(report["profile"]["role"]["code"], role["code"])
                self.assertEqual(report["profile"]["role"]["name"], role["name"])
                self.assertEqual(report["profile"]["role"]["source_task_ids"], ["task-role"])
                self.assertTrue(report["report_metadata"]["is_role_sufficient_info"])
                self.assertTrue(report["report_metadata"]["is_sufficient_info"])

    def test_r5_same_role_lands_on_different_index_levels(self):
        low = finalize_report(_role_draft("TABLE_GOBLIN", second_level="LOW"))
        high = finalize_report(_role_draft("TABLE_GOBLIN", second_level="HIGH"))

        self.assertEqual(low["profile"]["role"]["code"], high["profile"]["role"]["code"])
        self.assertNotEqual(low["metrics"]["irreplaceability_index"], high["metrics"]["irreplaceability_index"])

    def test_every_role_asset_file_exists_for_renderer(self):
        from pathlib import Path

        asset_dir = Path(__file__).resolve().parents[1] / "assets" / "characters"
        for role in ROLES:
            self.assertTrue((asset_dir / role["asset"]).is_file(), role["asset"])


class R1PredicateTest(unittest.TestCase):
    def test_predicate_requires_verb_object_and_signals_together(self):
        task = dict(ROLE_TASKS["TABLE_GOBLIN"])

        # 信号不满足 → 不命中。
        bad_signals = dict(task, signals=_signals(2, 2, 0, 1, 2, 2))
        self.assertNotIn("TABLE_GOBLIN", match_task_roles(bad_signals))

        # 动词缺失 → 不命中（对象与信号保留）。
        bad_verb = dict(task, task_name="多源数据周报", evidence="五个系统的运营数据与固定周报模板。")
        self.assertNotIn("TABLE_GOBLIN", match_task_roles(bad_verb))

        # 对象缺失 → 不命中（动词与信号保留）。
        bad_object = dict(task, task_name="多源信息搬运", evidence="从五个系统导出并清洗合并后录入。")
        self.assertNotIn("TABLE_GOBLIN", match_task_roles(bad_object))

        # 三者齐 → 命中。
        self.assertIn("TABLE_GOBLIN", match_task_roles(task))

    def test_unknown_tasks_never_match(self):
        unknown = dict(ROLE_TASKS["TABLE_GOBLIN"], exposure_level="UNKNOWN")
        self.assertEqual(match_task_roles(unknown), [])

    def test_task_text_uses_name_and_evidence_not_job_title(self):
        # 岗位名称不参与判定：证据里没有动词/对象就不命中。
        role_task = ROLE_TASKS["TABLE_GOBLIN"]
        task = dict(role_task, task_name="运营专员", evidence="负责整体协调与规划。")
        self.assertEqual(match_task_roles(task), [])

    def test_gatekeeper_accepts_either_judgment2_or_accountability2(self):
        base = ROLE_TASKS["GATEKEEPER_BEAR"]
        judgment_only = dict(base, signals=_signals(2, 0, 0, 1, 1, 2))
        accountability_only = dict(base, signals=_signals(1, 0, 0, 2, 1, 2))
        neither = dict(base, signals=_signals(1, 0, 0, 1, 1, 2))
        self.assertIn("GATEKEEPER_BEAR", match_task_roles(judgment_only))
        self.assertIn("GATEKEEPER_BEAR", match_task_roles(accountability_only))
        self.assertNotIn("GATEKEEPER_BEAR", match_task_roles(neither))


class R2R3WeightTest(unittest.TestCase):
    def test_user_share_decides_main_role(self):
        heavy = dict(ROLE_TASKS["INSPECTOR_BOT"], time_share_percent=70)
        light = dict(ROLE_TASKS["TABLE_GOBLIN"], time_share_percent=30)
        result = analyze_roles([heavy, light])

        self.assertEqual(result["main_role"], "INSPECTOR_BOT")
        self.assertEqual(result["coverage"], {"INSPECTOR_BOT": 70, "TABLE_GOBLIN": 30})

    def test_equal_fallback_counts_hits_when_no_shares(self):
        two = [dict(ROLE_TASKS["TRANSLATOR_FOX"], time_share_percent=None),
               _task("task-t2", "对齐第二组", "再次对齐两个团队的需求信息。", "MEDIUM", None, ROLE_TASKS["TRANSLATOR_FOX"]["signals"])]
        one = [dict(ROLE_TASKS["PROGRESS_HERDER"], time_share_percent=None)]
        self.assertEqual(analyze_roles(two + one)["main_role"], "TRANSLATOR_FOX")

    def test_mixed_input_uses_single_formula_with_equal_weight_one(self):
        # 混合输入同一公式：搬表兽 25（用户占比）；催办兽 24（用户占比）+ 两条缺失占比（各按 1）= 26。
        shared = dict(ROLE_TASKS["TABLE_GOBLIN"], time_share_percent=25)
        user_share = dict(ROLE_TASKS["PROGRESS_HERDER"], time_share_percent=24)
        missing_a = dict(ROLE_TASKS["PROGRESS_HERDER"], time_share_percent=None)
        missing_b = dict(ROLE_TASKS["PROGRESS_HERDER"], time_share_percent=None, task_id="task-herder-2", evidence="跟进排期，催办延期依赖并更新里程碑。")
        result = analyze_roles([shared, user_share, missing_a, missing_b])

        self.assertEqual(result["main_role"], "PROGRESS_HERDER")
        self.assertEqual(result["coverage"]["PROGRESS_HERDER"], 26)
        self.assertEqual(result["coverage"]["TABLE_GOBLIN"], 25)

    def test_r3_tie_breaks_by_table_order(self):
        # 等权重并列：翻译兽(7) 先于 催办兽(9)；搬表兽(1) 先于 巡检兽(2)。
        late_order = analyze_roles([
            dict(ROLE_TASKS["PROGRESS_HERDER"], time_share_percent=50),
            dict(ROLE_TASKS["TRANSLATOR_FOX"], time_share_percent=50),
        ])
        early_order = analyze_roles([
            dict(ROLE_TASKS["INSPECTOR_BOT"], time_share_percent=50),
            dict(ROLE_TASKS["TABLE_GOBLIN"], time_share_percent=50),
        ])
        self.assertEqual(late_order["main_role"], "TRANSLATOR_FOX")
        self.assertEqual(early_order["main_role"], "TABLE_GOBLIN")


class R4DualThresholdTest(unittest.TestCase):
    def test_index_threshold_fails_role_and_index_hidden(self):
        result = analyze_roles([
            ROLE_TASKS["TABLE_GOBLIN"],
            dict(NEUTRAL_TASK, exposure_level="UNKNOWN"),
            _task("task-vague-2", "综合协调", "负责综合协调事务。", "UNKNOWN", None, _signals(), "LOW"),
        ])
        self.assertFalse(result["is_role_sufficient"])
        self.assertEqual(result["main_role"], None)

    def test_role_threshold_can_fail_while_index_threshold_passes(self):
        # 3/3 暴露可判（指数门槛过），但只有 1 条命中角色（角色门槛未过）。
        tasks = [
            ROLE_TASKS["TABLE_GOBLIN"],
            dict(NEUTRAL_TASK, exposure_level="MEDIUM"),
            _task("task-neutral-2", "跨团队例会", "主持跨团队例会并口头汇报进展。", "LOW", None, _signals(1, 1, 0, 1, 1, 1)),
        ]
        result = analyze_roles(tasks)
        self.assertEqual(result["role_evaluable"], 1)
        self.assertFalse(result["is_role_sufficient"])
        self.assertIsNone(result["main_role"])

    def test_exactly_half_role_evaluable_is_sufficient(self):
        result = analyze_roles([ROLE_TASKS["TABLE_GOBLIN"], NEUTRAL_TASK])
        self.assertTrue(result["is_role_sufficient"])


class CoexistenceStateTest(unittest.TestCase):
    def _coexistence_draft(self):
        draft = _role_draft("TABLE_GOBLIN")
        # 把第二条任务换成零命中的可判断任务 → 指数显示、角色门槛未过。
        draft["tasks"][1] = dict(NEUTRAL_TASK, exposure_level="MEDIUM")
        draft["tasks"].append(
            _task("task-neutral-2", "跨团队例会", "主持跨团队例会并口头汇报进展。", "LOW", None, _signals(1, 1, 0, 1, 1, 1))
        )
        for task in draft["tasks"][1:]:
            task["time_share_percent"] = None
        draft["tasks"][0]["time_share_percent"] = None
        return draft

    def test_parallel_state_shows_real_index_with_shadow_beast(self):
        report = finalize_report(self._coexistence_draft())

        assert_valid_report(report)
        self.assertIsNotNone(report["metrics"]["irreplaceability_index"])
        self.assertEqual(report["profile"]["role"]["code"], "SHADOW_BEAST")
        self.assertEqual(report["profile"]["role"]["name"], "影子兽 · 待解锁工种")
        self.assertEqual(report["profile"]["role"]["source_task_ids"], [])
        self.assertFalse(report["report_metadata"]["is_role_sufficient_info"])
        self.assertTrue(report["report_metadata"]["is_sufficient_info"])
        # 并存态分享卡：真指数 + 影子兽名。
        self.assertEqual(report["share_card"]["irreplaceability_index"], report["metrics"]["irreplaceability_index"])
        self.assertEqual(report["share_card"]["role_name"], "影子兽 · 待解锁工种")

    def test_parallel_state_keeps_case_snarky_quote_without_role_identity(self):
        draft = self._coexistence_draft()
        draft["profile"]["role"]["snarky_quote"] = "三摊子事各说各话，全靠你本人兼容。"

        report = finalize_report(draft)

        self.assertEqual(report["profile"]["role"]["code"], "SHADOW_BEAST")
        self.assertEqual(report["profile"]["role"]["snarky_quote"], "三摊子事各说各话，全靠你本人兼容。")

    def test_full_insufficient_state_hides_index_and_uses_shadow(self):
        draft = _role_draft("TABLE_GOBLIN")
        for task in draft["tasks"]:
            task["exposure_level"] = "UNKNOWN"
            task["time_share_percent"] = None
            task["signals"] = _signals()
        for action in draft["action_plan"].values():
            action["source_task_ids"] = ["task-weekly-sync"]
        draft["tasks"][1]["task_id"] = "task-weekly-sync"
        draft["human_edge"][0]["source_task_ids"] = ["task-weekly-sync"]

        report = finalize_report(draft)

        self.assertIsNone(report["metrics"]["irreplaceability_index"])
        self.assertEqual(report["profile"]["role"]["code"], "SHADOW_BEAST")
        self.assertFalse(report["report_metadata"]["is_sufficient_info"])


class DeterminismTest(unittest.TestCase):
    def test_same_tasks_always_yield_same_role(self):
        tasks = [ROLE_TASKS["GATEKEEPER_BEAR"], NEUTRAL_TASK]
        first = analyze_roles(tasks)
        second = analyze_roles([dict(task) for task in tasks])
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
