# 1.0.0 → 2.0.0 迁移说明

契约版本：`1.0.0` → `2.0.0`（`schema_version` 与 `rule_version` 同步升级）。
触发变更：角色体系由旧六角色升级为 12 类＋影子兽（内容基线冻结版，见 `docs/SCORING_RULES.md` §6）。
**指数算法、任务等级判定与聚合语义完全未动**——同一份任务输入在两个版本下得到相同的
`exposure_index` / `exposure_level` / `raw_score` / `weight_mode`。

## 字段级变化

| 位置 | 1.0.0 | 2.0.0 |
| --- | --- | --- |
| `profile.role.code` | 旧六角色枚举 + `LOCKED_ROLE` | 12 类新枚举 + `SHADOW_BEAST` |
| `profile.situation_paragraph` | 无 | 新增必填（处境白描） |
| `profile.index_note` | 无 | 新增必填（首屏指数说明小字） |
| `tasks[].role_codes` | 无 | 新增（该任务命中的角色 code 列表；UNKNOWN/零命中为 `[]`） |
| `metrics.task_count_role_evaluable` | 无 | 新增（至少命中一个角色的任务条数） |
| `report_metadata.is_role_sufficient_info` | 无 | 新增（主角色门槛是否通过） |

## 角色迁移映射（冻结版②）

旧角色 code 不做一对一映射，**由角色匹配引擎（`scripts/role_match.py`，R1–R5）按任务证据重判**。
冻结版给出的候选映射作为验收参照：

| 旧角色 | 候选新角色 |
| --- | --- |
| `FLOW_ORCHESTRATOR` 流程编排员 | 搬表兽 / 巡检兽 / 催办兽 |
| `CONTENT_CALIBRATOR` 内容校准师 | 校稿兽 / 拼装兽 |
| `SYSTEM_BOUNDARY_GUARD` 系统边界守门人 | 守门兽 |
| `COORDINATION_TRANSLATOR` 多方协同译码员 | 翻译兽 / 拆解兽 / 解题兽 |
| `PROJECT_RISK_NAVIGATOR` 项目风险领航员 | 排雷兽 / 应变兽（应变兽仅当任务现场信号 ≥1 才可能命中） |
| `LOCKED_ROLE` 待解锁职业角色 | 影子兽（SHADOW_BEAST） |

数据追因类工作原散落在“流程编排员（异常协同）”与“译码员”中，迁移时按“对象是原因还是信息”由引擎重判。

## 门槛语义变化（R4 双门槛）

- 1.0.0：单一门槛 `is_sufficient_info` 同时控制指数显示与 `LOCKED_ROLE` 兜底。
- 2.0.0：两道门槛独立——
  - 指数门槛：暴露可判任务（LOW/MEDIUM/HIGH）× 2 ≥ 全部任务数，否则不显示总指数；
  - 主角色门槛：角色可判任务（至少命中一个角色）× 2 ≥ 全部任务数，否则显示影子兽。
- 因命中任务 ⊆ 暴露可判任务，“无指数却有主角色”不可能出现；
  **“有指数＋影子兽”并存态允许存在**（指数是真数字，角色位是待解锁形象）。

## 迁移方式

- 草稿（draft）：`finalize_report.py` 读时迁移——1.0.0 与 2.0.0 草稿都被接受，
  角色一律由引擎重判，产物固定为 2.0.0。
- 已交付的 1.0.0 final 报告：`python3 scripts/migrate_report.py --input old.json --output new.json`，
  迁移后指数与等级逐字段不变，仅角色体系与新增字段变化。

## 同步状态

`references/report-contract.schema.json`、`scripts/validate_report.py` 已随本说明同步至 2.0.0；
`docs/SCORING_RULES.md` §6 为角色体系的规则权威。
