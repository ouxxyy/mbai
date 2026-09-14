"""4.1 动宾词表受控扩展（rule_version 4.1.0）契约测试。

来源：prompt-engineer 4.1 映射设计（MYW-70，2026-09-14）＋ analyst §四受控协议：
- 14 条正反例（7 正 7 反）逐条落测试；
- 13 个既有样例主角色不变量（仿真固化为测试）；
- 3 个知识型样例按设计期望断言（含双命中）；
- 反事实回归：供应商对象若入翻译工对象表将翻转 project-owner——锁定该约束。
"""

import unittest
from copy import deepcopy

from scripts.finalize_report import finalize_report
from scripts.role_match import ROLES, analyze_roles, match_task_roles
from scripts.sample_cases import case_definitions, draft_for_case

S = lambda j, c, p, a, r, d: {
    "judgment": j, "coordination": c, "physical_presence": p,
    "accountability": a, "repeatability": r, "digital_input_output": d,
}


def _task(name, evidence, signals):
    return {"task_name": name, "evidence": evidence, "exposure_level": "MEDIUM", "signals": signals}


class PositiveExamplesTest(unittest.TestCase):
    """应命中（7 条）。"""

    def test_ex1a_standard_setting_hits_proofreader_only(self):
        task = _task("制定产品功效宣称的统一规范", "制定产品功效宣称的统一规范并维护。", S(2, 0, 0, 1, 0, 2))
        self.assertEqual(match_task_roles(task), ["PROOFREADER_WORKER"])

    def test_ex1b_policy_drafting_hits_proofreader_only(self):
        task = _task("拟定供应商季度考核制度", "拟定供应商季度考核制度与评分标准。", S(1, 1, 0, 1, 0, 2))
        self.assertEqual(match_task_roles(task), ["PROOFREADER_WORKER"])

    def test_ex2a_building_flow_hits_deconstructor_only(self):
        task = _task("从零搭建合同审批流程", "从零搭建合同审批流程并组织试用。", S(2, 0, 0, 1, 0, 2))
        self.assertEqual(match_task_roles(task), ["DECONSTRUCTOR_WORKER"])

    def test_ex2b_optimizing_flow_hits_deconstructor_only(self):
        task = _task("优化报销审批流程", "优化报销审批流程，五环节压三环节。", S(2, 0, 0, 1, 1, 2))
        self.assertEqual(match_task_roles(task), ["DECONSTRUCTOR_WORKER"])

    def test_ex2c_building_system_hits_deconstructor_only(self):
        task = _task("建立跨部门数据共享体系", "建立跨部门数据共享体系与维护制度。", S(2, 1, 0, 1, 0, 2))
        self.assertEqual(match_task_roles(task), ["DECONSTRUCTOR_WORKER"])

    def test_ex3_vendor_management_hits_solver_only(self):
        task = _task("对接供应商管理交付节奏", "对接供应商管理交付节奏，例外时协商补救。", S(1, 2, 0, 1, 0, 1))
        self.assertEqual(match_task_roles(task), ["SOLVER_WORKER"])

    def test_ex7_schedule_planning_multi_hits_inspector_and_progress(self):
        task = _task("规划季度发布排期并跟进关键依赖", "规划季度发布排期并跟进关键依赖。", S(1, 1, 0, 1, 2, 2))
        self.assertEqual(set(match_task_roles(task)), {"INSPECTOR_WORKER", "PROGRESS_WORKER"})


class NegativeExamplesTest(unittest.TestCase):
    """邻近角色不得命中（7 条）。"""

    def test_ex8_execution_is_not_building(self):
        # 例句按真实词表微调：携带巡检工对象（链接/库存/字段），反例断言（拆解工不得命中）不变。
        task = _task(
            "按既定流程每日配置并发布商品上架",
            "按既定流程每日配置并发布商品上架，逐项检查链接与库存字段。",
            S(0, 0, 0, 1, 2, 2),
        )
        self.assertEqual(match_task_roles(task), ["INSPECTOR_WORKER"])

    def test_ex9_breaking_ideas_is_not_setting_standards(self):
        task = _task("把老板一句话拆解成采购流程清单", "把老板一句话拆解成采购流程清单。", S(2, 0, 0, 1, 1, 1))
        self.assertEqual(match_task_roles(task), ["DECONSTRUCTOR_WORKER"])

    def test_ex10_internal_alignment_is_not_solving(self):
        task = _task("协调产品与研发对齐需求优先级", "协调产品与研发对齐需求优先级。", S(1, 2, 0, 1, 0, 2))
        self.assertEqual(match_task_roles(task), ["TRANSLATOR_WORKER"])

    def test_ex11_vendor_incident_stays_minesweeper_and_onscene(self):
        task = _task("供应商设备突发故障时到现场协调处置", "供应商设备突发故障时到现场协调处置并承担结果。", S(2, 2, 2, 2, 0, 1))
        self.assertEqual(set(match_task_roles(task)), {"MINESWEEPER_WORKER", "ONSCENE_WORKER"})

    def test_ex12_operations_regression_signal_gate_blocks_progress(self):
        task = _task("按排期在后台配置并发布活动内容", "按排期在后台配置并发布活动内容，检查链接和库存字段。", S(0, 0, 0, 1, 2, 2))
        self.assertEqual(match_task_roles(task), ["INSPECTOR_WORKER"])

    def test_ex13_budget_planning_hits_nothing(self):
        task = _task("规划部门年度预算分配方案", "规划部门年度预算分配方案并汇报。", S(2, 1, 0, 2, 0, 1))
        self.assertEqual(match_task_roles(task), [])

    def test_ex14_optimize_layout_stays_assembly(self):
        task = _task("优化专题页排版与素材", "整理排版专题页素材并多版本更新。", S(0, 0, 0, 1, 2, 2))
        self.assertEqual(match_task_roles(task), ["ASSEMBLY_WORKER"])


class LegacyInvariantTest(unittest.TestCase):
    """13 个既有样例主角色不变量（analyst §四规则 4：测试锁死）。"""

    EXPECTED = {
        "operations-repetitive": "TABLE_WORKER",
        "content-calibrator": "ASSEMBLY_WORKER",
        "technical-execution": "GATEKEEPER_WORKER",
        "client-coordination": "TRANSLATOR_WORKER",
        "project-owner": "ONSCENE_WORKER",
        "sparse-information": None,  # 引擎层 main_role=None ⇔ finalize 落神秘工
        "risk-owner-showcase": "MINESWEEPER_WORKER",
        "ops-shallow": "INSPECTOR_WORKER",
        "ops-deep": None,
        "writing-detailed": "ASSEMBLY_WORKER",
        "writing-concise": "ASSEMBLY_WORKER",
        "operations-injection": "TABLE_WORKER",
        "operations-demographics": "TABLE_WORKER",
    }

    def test_all_legacy_cases_keep_their_main_roles(self):
        cases = {case["slug"]: case for case in case_definitions()}
        for slug, expected in self.EXPECTED.items():
            with self.subTest(slug=slug):
                result = analyze_roles(cases[slug]["tasks"])
                self.assertEqual(result["main_role"], expected)


class KnowledgeSampleTest(unittest.TestCase):
    """3 个知识型样例按 4.1 设计期望断言（含权重主角色与取档锚点）。"""

    def test_flow_builder_lands_on_deconstructor(self):
        cases = {case["slug"]: case for case in case_definitions()}
        report = finalize_report(draft_for_case(cases["knowledge-flow-builder"]))
        self.assertEqual(report["profile"]["role"]["code"], "DECONSTRUCTOR_WORKER")
        self.assertEqual(report["metrics"]["raw_score"], 37.5)  # 半档向上：取整 40
        self.assertEqual(report["metrics"]["irreplaceability_index"], 60)

    def test_standard_owner_lands_on_proofreader(self):
        cases = {case["slug"]: case for case in case_definitions()}
        report = finalize_report(draft_for_case(cases["knowledge-standard-owner"]))
        self.assertEqual(report["profile"]["role"]["code"], "PROOFREADER_WORKER")
        self.assertEqual(report["metrics"]["raw_score"], 77.5)  # 半档向上：取整 80
        self.assertEqual(report["metrics"]["irreplaceability_index"], 20)

    def test_vendor_manager_lands_on_solver(self):
        cases = {case["slug"]: case for case in case_definitions()}
        report = finalize_report(draft_for_case(cases["knowledge-vendor-manager"]))
        self.assertEqual(report["profile"]["role"]["code"], "SOLVER_WORKER")
        self.assertEqual(report["metrics"]["raw_score"], 62.5)  # 半档向上：取整 65
        self.assertEqual(report["metrics"]["irreplaceability_index"], 35)


class CounterfactualVendorConstraintTest(unittest.TestCase):
    """反事实回归：供应商对象不得入翻译工对象表（否则 project-owner 主角色翻转）。"""

    def test_vendor_object_in_translator_would_flip_project_owner(self):
        import scripts.role_match as role_match

        cases = {case["slug"]: case for case in case_definitions()}
        original_table = deepcopy(role_match.ROLES)
        original_by_code = role_match.ROLE_BY_CODE
        original_names = role_match.ROLE_NAMES
        try:
            for role in role_match.ROLES:
                if role["code"] == "TRANSLATOR_WORKER":
                    role["objects"] = list(role["objects"]) + ["供应商"]
            flipped = analyze_roles(cases["project-owner"]["tasks"])["main_role"]
            self.assertEqual(flipped, "TRANSLATOR_WORKER", "反事实未生效，测试前提失效")
        finally:
            role_match.ROLES = original_table
            role_match.ROLE_BY_CODE = original_by_code
            role_match.ROLE_NAMES = original_names
        # 真实词表下必须仍是应变工。
        self.assertEqual(
            analyze_roles(cases["project-owner"]["tasks"])["main_role"],
            "ONSCENE_WORKER",
        )


class VocabularyBoundaryTest(unittest.TestCase):
    """泛动词禁令：新增词不得为裸泛动词（analyst §四规则 2）。"""

    BANNED_BARE_VERBS = {"管理", "负责", "跟进", "参与", "支持", "统筹", "规划", "设计", "开发"}
    ALLOWED_EXISTING = {"跟进"}  # 既有裸动词（催办工），协议只加不改

    def test_no_new_bare_generic_verbs_entered_tables(self):
        for role in ROLES:
            bare = (self.BANNED_BARE_VERBS - self.ALLOWED_EXISTING) & set(role["verbs"])
            self.assertEqual(bare, set(), f"{role['code']} 含禁用裸泛动词：{bare}")


if __name__ == "__main__":
    unittest.main()
