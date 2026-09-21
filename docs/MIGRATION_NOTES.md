# 5.0 迁移补充

5.0 删除关键词分类引擎与神秘类别；旧名称映射仅作历史记录，不再决定分类。旧报告必须由模型根据新 12 类补写 code、reason、confidence、source_task_ids，以及分享 value_line/source_task_ids，删除旧分享 task_highlights/proof_7d。缺分类信息返回 ROLE_REANALYSIS_REQUIRED，禁止静默猜类。指数按原任务重新聚合，不能二次翻转；保留原文件。

## 5.1.0 迁移补充（2026-09-22）

内容基线改版：诊断主线五步、三个行动展示名（`改造任务 / 练习关键判断 / 留下求职证据`，
契约字段名不变，见 ADR 0002）、处境结论结构与人群口径更新。**字段结构、评分算法与聚合
语义完全未动**——同一份任务输入在 5.0.0 与 5.1.0 下得到相同的 `raw_score` /
`irreplaceability_index` / `irreplaceability_level`（回归锚点算例：technical-execution
raw 47.5 → 50 · 中不可替代）。

- 迁移方式：`python3 scripts/migrate_report.py --input old.json --output new.json`。
  5.0.0 final 报告迁移后版本印记升为 5.1.0，指数与等级逐字段不变。
- **无损约束**：处境结论、优势边界与三个行动文案逐字保留；旧报告中的旧行动建议**不回写
  新展示名**（ADR 0002），旧建议不得冒充新版诊断。角色昵称按当前角色表刷新（沿用既有
  迁移行为，如 守门工 → 上线守门员）。
- 原件不覆盖：迁移只写 `--output`，输入文件保持原样。
- 渲染行为：5.1.0 渲染器固定标签为新展示名；对迁移报告重新渲染会以新标签呈现旧建议，
  旧建议文本本身未改写。

以下为历史记录，不是当前生成规则。

# 迁移说明（1.0.0 → 2.0.0 → 3.0.0 → 4.0.0 → 4.1.0）

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

## 2.0.0 → 3.0.0：展示层语义翻转（2026-09-13，产品决策）

对外指标由「AI 替代指数」改为「**AI 不可替代指数**」。**指数聚合算法与任务等级判定完全未动，
翻转只发生在展示层**（唯一函数 `scripts/display_metrics.py`：显示分 = 100 − 取整后替代分，
先取整、后取补；等级按翻转表 HIGH↔LOW / MEDIUM↔MEDIUM 镜像）。

| 位置 | 2.0.0 | 3.0.0 |
| --- | --- | --- |
| `metrics.exposure_index / exposure_level` | 替代口径 | 重命名为 `irreplaceability_index / irreplaceability_level`（翻转后取值） |
| `share_card.exposure_index / exposure_level` | 同上 | 同步重命名 |
| `metrics.raw_score` | 替代原始分 | **字段名与语义原样保留**（可追溯锚） |
| `tasks[].exposure_level / score` | 任务级替代 | **不改**（描述任务的 AI 可完成度） |

- 展示带域镜像：≤20 低不可替代 / 25–60 中不可替代 / ≥65 高不可替代。
- 旧案例展示值翻转（产品决策，**有意推翻** Phase 2 的“指数与等级保持一致”验收项的展示面）：
  operations-repetitive 90/HIGH → **10/LOW**；ops-deep 55/MEDIUM → **45/MEDIUM**；信息不足态不变。
- 防双翻：`migrate_report.py` 拒绝迁移 3.0.0 报告（幂等由测试锁定）；1.0.0/2.0.0 草稿读时迁移。
- 颜色绑定随风险镜像：新 LOW/MEDIUM（高替代风险）＝警示橙，新 HIGH（安全）＝品牌黄/黑。

## 3.0.0 → 4.0.0：角色更名与品牌化（2026-09-14）

**机械更名、零语义**：12+1 角色昵称由「xx兽」改为「xx工」，code 全量迁移为 `*_WORKER`，素材文件同步改名（`assets/characters/*_worker.webp`），新增工牌短码 `TW-01…TW-12 / TW-00`；品牌层引入 `mbai`（Me, Beyond AI）——`mbai` 是测评品牌名，「工作任务 AI 不可替代指数」仍是正式指标名，分数/等级/算法/判定零改动。**指数算法、R1–R5 命中谓词、信号约束、表序全部未动**；角色像素素材沿用现有图像，后续视觉批次按同名文件直接替换。

| 3.x 昵称（code） | 4.0.0 昵称（code） | 工牌 |
| --- | --- | --- |
| 搬表兽 · 表格搬运官（TABLE_GOBLIN） | 搬表工（TABLE_WORKER） | TW-01 |
| 巡检兽 · 流程巡航员（INSPECTOR_BOT） | 巡检工（INSPECTOR_WORKER） | TW-02 |
| 校稿兽 · 口径校准员（PROOFREADER_OWL） | 校稿工（PROOFREADER_WORKER） | TW-03 |
| 拼装兽 · 素材组装手（ASSEMBLY_CRANE） | 拼装工（ASSEMBLY_WORKER） | TW-04 |
| 追因兽 · 归因探查员（ROOTCAUSE_HOUND） | 追因工（ROOTCAUSE_WORKER） | TW-05 |
| 守门兽 · 上线守门员（GATEKEEPER_BEAR） | 守门工（GATEKEEPER_WORKER） | TW-06 |
| 翻译兽 · 信息对齐官（TRANSLATOR_FOX） | 翻译工（TRANSLATOR_WORKER） | TW-07 |
| 拆解兽 · 清单拆解手（DECONSTRUCTOR_BEAVER） | 拆解工（DECONSTRUCTOR_WORKER） | TW-08 |
| 催办兽 · 进度推土机（PROGRESS_HERDER） | 催办工（PROGRESS_WORKER） | TW-09 |
| 排雷兽 · 风险预警员（MINESWEEPER_MOLE） | 排雷工（MINESWEEPER_WORKER） | TW-10 |
| 解题兽 · 现场解题手（SOLVER_OTTER） | 解题工（SOLVER_WORKER） | TW-11 |
| 应变兽 · 实时响应员（ONSCENE_CHAMELEON） | 应变工（ONSCENE_WORKER） | TW-12 |
| 影子兽 · 待解锁工种（SHADOW_BEAST） | 神秘工 · 待解锁（SHADOW_WORKER） | TW-00 |

- 三层迁移链：1.0.0 / 2.0.0 / 3.0.0 草稿与 final 均可读时或显式迁移至 4.0.0（角色由引擎按任务证据重判，code 落在新枚举）；4.0.0 报告拒绝再迁移（幂等测试锁定）。
- 品牌露出：分享卡顶栏左侧 mbai 徽章、HTML ticker 徽章、HTML 页脚锁定语 `mbai — Me, Beyond AI · 我，在 AI 之上`（品牌资产在 `assets/brand/`，SVG 全为闭合路径矢量）。
- 指数展示口径不变：仍是 3.0.0 的「先取整、后取补」不可替代指数。
- **4.0.0 → 4.1.0（2026-09-14）**：仅 `rule_version` 升版（schema_version 保持 4.0.0）——动宾词表受控扩展（四角色只增 verbs/objects，见 SCORING_RULES §6 增补块）；13 个既有样例主角色不变（测试锁定）；旧报告无字段变化，无需迁移。

## 同步状态

`references/report-contract.schema.json`、`scripts/validate_report.py` 已随本说明同步至 4.0.0；
`docs/SCORING_RULES.md` §6 为角色体系的规则权威，§1/§3 的 3.0.0 增补块为展示口径权威。
