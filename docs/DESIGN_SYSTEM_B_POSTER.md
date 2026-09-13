# AI 任务不可替代指数 · B 方向统一视觉设计规范

> **4.0.0 机械同步（2026-09-14，developer）**：角色昵称/代号/素材文件名随 4.0.0 全量更名为「xx工 / *_WORKER / *_worker.webp」并新增工牌短码 TW-01…TW-00；品牌层新增 `assets/brand/`（mbai 徽章与字标，闭合路径矢量）。本规范的角色形象章节（§三/§五）仍描述首代造型（历史记录），**视觉家族由「工牌绒绒」方向取代，待 designer 全量资产按同名文件替换后更新本规范**；文件名与颜色 Token 即当前契约。
**Design System: Swiss Neo-Brutalism Attitude Poster (新瑞士式态度海报)**

---

## 一、设计哲学与核心心智 (Design Philosophy)

1. **去 AI 廉价感，树立硬核态度**：
   - 彻底摒弃通用的 AI 紫蓝渐变与后台仪表盘廉价感；
   - 采用国际先锋的**新瑞士粗野主义（Swiss Neo-Brutalism）**排印风格：以极端反差的明黄（`#EBFB3B`）、深炭黑（`#0D0D0D`）与警示橙（`#FF4A00`）构建极强的视觉张力；
   - 以**“态度海报”**与**“硬核职业体检”**为第一心智，让用户在微信对话与朋友圈中第一眼被冲击，产生强烈的共鸣与转发欲。

2. **严谨的专业底线声明（分层承担，2026-09-13 冻结）**：
   - **HTML 报告页**保留指标解释声明，在首屏 ticker、正文与折叠区（方法与边界）常态化出现：
     > **“不可替代指数量的也是任务，不是人。”**
   - **分享卡**角落由获欧八显式授权的引流文案承担（见 §4.3）；指标解释不强行以同文案挤占卡片角落——两层各司其职，不要求同文案；
   - 强化客观、克制、严谨、不吓人、不制造职场焦虑的品牌底线。

3. **潮玩盲盒家族（同物种 · 轮廓优先；4.0.0 起视觉方向为「工牌绒绒」，见文首注）**：
   - 统一角色原型：敦实、微胖、大头短四肢、哑光材质（首代为树脂；绒绒代为植绒）；
   - **严禁单纯换色**：100% 依靠动作动态、身体姿态、表情神韵与**标志性专属道具**构建轮廓差异，确保在手机缩略图或 48px 小头像下 0.5 秒即可一眼识别工种。

---

## 二、色彩系统 (Color System)

| 色彩角色 | 变量名 | HEX 色值 | RGB 色值 | 适用场景与语义 |
| :--- | :--- | :--- | :--- | :--- |
| **主基调黄 (Neon Yellow)** | `--c-yellow` | `#EBFB3B` | `rgb(235, 251, 59)` | 巨号指数、重要金句嘴替背景、主按钮、顶部警示条文字 |
| **高反差黑 (Deep Black)** | `--c-black` | `#0D0D0D` | `rgb(13, 13, 13)` | 核心重力态度块、硬边框、极粗文字、阴影深色 |
| **警示高亮橙 (Alert Orange)** | `--c-orange` | `#FF4A00` | `rgb(255, 74, 0)` | HIGH 等级标贴、微倾斜小标签、硬投影强调色、关键警示线 |
| **中立微灰 (Neutral Light)** | `--c-gray-light` | `#F4F4F0` | `rgb(244, 244, 240)` | 全局底色、卡片衬底、次级容器背景 |
| **卡片纯白 (Clean White)** | `--c-white` | `#FFFFFF` | `rgb(255, 255, 255)` | 白描纸张卡片、正文字体、卡块高亮反白 |
| **辅助深灰 (Charcoal Dark)** | `--c-dark-card` | `#1A1A1A` | `rgb(26, 26, 26)` | 黑色卡块内部嵌套小模块、折叠区面板底色 |
| **边框颜色 (Border Black)** | `--c-border` | `#0D0D0D` | `rgb(13, 13, 13)` | 全局统一 3.5px / 3px 硬实线边框 |

---

## 三、字体与排印层级系统 (Typography Hierarchy)

### 3.1 字体栈定义
```css
:root {
  --font-heavy: "Impact", "Arial Black", -apple-system, BlinkMacSystemFont, "PingFang SC", "Heiti SC", sans-serif;
  --font-sans: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  --font-mono: "SF Mono", "Consolas", "Monaco", "Courier New", monospace;
}
```

### 3.2 字阶规范
| 语义层级 | 字号 (Desktop) | 字号 (Mobile) | 字重 | 行高 | 字体族 | 样例应用 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **巨号指数 (Giant Score)** | 168px | 120px | 900+ Heavy | 0.82 | `--font-heavy` | `90`, `85`, `95` |
| **等级大标 (Level Large)** | 40px | 28px | 900+ Heavy | 1.0 | `--font-heavy` | `HIGH`, `MEDIUM` |
| **角色正式名 (Character Title)**| 34px | 26px | 900+ Heavy | 1.2 | `--font-sans` | `搬表工` |
| **态度嘴替 (Statement Banner)** | 26px | 19px | 900+ Heavy | 1.35 | `--font-heavy` | `六个平台互不相通，全靠你本人兼容。` |
| **区块标题 (Section H2)** | 28px | 22px | 900+ Heavy | 1.3 | `--font-sans` | `01 哪句话说中了我` / `处境白描` |
| **正文主字 (Body Prose)** | 16px | 15px | 400 Regular | 1.65 | `--font-sans` | 处境白描叙述、分工细节说明 |
| **标签/参数条 (Ticker & Meta)** | 13px | 11px | 700 Bold | 1.2 | `--font-mono` | `STATUS: ACTIVE // ROUND_HALF_UP_TO_5` |
| **说明小字 (Disclaimer)** | 14px | 12px | 500 Medium | 1.5 | `--font-sans` | `替代指数量的是任务，不是人……` |

---

## 四、三端构图骨架与安全边界 (Layout Skeletons)

### 4.1 桌面端 (1440×900+ 基准)
- **栅格比例**：左右不对称撞色栅格 `grid-template-columns: 1.15fr 0.85fr; gap: 28px;`
- **左侧重力态度块**：
  - 深炭黑底色（`#0D0D0D`），白色正文字体，内置 3.5px 硬黑色边框与 `10px 10px 0px rgba(0,0,0,0.15)` 投影；
  - 承载巨号指数（168px 亮黄）、等级标牌、角色全称、亮黄色微倾斜（`0.5deg`）态度嘴替横幅、说明小字。
- **右侧潮玩展台块**：
  - 明亮黄底色（`#EBFB3B`），内置 3.5px 黑色硬边框；
  - 顶部陈列序列号胶囊（`SPECIMEN NO.01`）与代号；
  - 核心展示仓采用 460px 透明底潮玩立像，下垫黑色实体椭圆展台底座；
  - 底部铭牌标出该工种标志性道具与核心职能。

### 4.2 移动端首屏 (390×844 严格自适应保护)
- **单列垂直流**：
  - 严禁任何绝对定位硬切视口，必须添加断行保护：`word-break: break-word; overflow-wrap: break-word; min-width: 0;`；
  - 顶部公告栏（`.poster-ticker`）自适应换行，次要 meta 在超窄视口下自动折叠；
  - 巨号指数缩小至 120px，保持在第一屏内居中立显；
  - 角色立像控制在 240px 级，紧跟指数下方，确保“指数 + 角色 + 嘴替金句”首屏无需滚动即可一屏收拢。

### 4.3 微信分享卡 (1080×1440 黄金比例卡面)
- **绝对视觉重心**：
  - 上方 60% 面积归属大指数（150px）与潮玩立像（420px），构成第一眼视觉锚点；
  - 下方 40% 面积收拢“一句话嘴替”、“分工速览”与“7 天行动下一步”；
  - **必备角落引导语**（欧八 2026-09-13 显式授权保留，对应 MYW-70 冻结记录）：底部左下角固定印制 `“搜 欧八同学 生成自己的职业AI体检报告”`，右下角标注评级代码；指标解释声明按 §一.2 分层规则由 HTML 报告页承担。

---

## 五、12 角色 + 1 待解锁（神秘工）全量矩阵与打磨口径

### 5.1 口径审查与修订说明（吸收 Reviewer 复核意见）
1. **追因工**：
   - 原口径：“数字不对的时候，全世界都问你为什么”（存在被动被追责与人际窒息感）；
   - **终审定稿口径**：**“报表异常只是表象，顺着链路定位根因的是你。”**（强调系统性溯源能力，专业克制）。
2. **守门工**：
   - 原口径：“出事之前没人看见你，出事之后所有人都找你”（存在背锅负面心理暗示）；
   - **终审定稿口径**：**“拦截隐患于发生之前，把关质量于交付之初。”**（强调质量守门人的主动把关权力与稳固价值）。

### 5.2 13 只角色完整设定矩阵表 (A1/A2 工牌绒绒家族正式定稿)
| 编号 | 正式名称 | 英文代号 | 一句话定义句 (打磨定稿) | 标志性道具与体型骨架 (6:6平衡) | 专属辅助色 | 素材文件名 (800×800 WebP ≤150KB) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **01** | **搬表工** | `TABLE_WORKER · TW-01` | 你把数据从 A 搬到 B，顺便当格式转换器。 | 【稳态·水桶型】手捧立体发光绿色 Excel 键帽 / 数据表格板，胸前挂 TW-01 白底工牌 | 薄荷绿 (#22C55E) | `01_table_worker.webp` (34.1 KB) |
| **02** | **巡检工** | `INSPECTOR_WORKER · TW-02` | 按清单跑流程，链接、字段、库存，一个都不能错。 | 【稳态·方墩型】手持超大高亮工业放大镜，胸前长清单纸带，头顶旋转警报小灯，挂 TW-02 工牌 | 扫描青蓝 (#0EA5E9) | `02_inspector_worker.webp` (34.1 KB) |
| **03** | **校稿工** | `PROOFREADER_WORKER · TW-03` | 同一句话要说给不同的人听，你保证它每次都说得对。 | 【稳态·敦厚型】复古老花镜，斜扛巨型红色删除号铅笔与贴标卷纸，挂 TW-03 工牌 | 校对橙红 (#EA580C) | `03_proofreader_worker.webp` (42.2 KB) |
| **04** | **拼装工** | `ASSEMBLY_WORKER · TW-04` | 素材从四面八方来，成品从你手里出去。 | 【稳态·宽肩型】双手握模块化螺丝刀组，抱持发光蓝色积木卡榫方盒，挂 TW-04 工牌 | 工业浅蓝 (#38BDF8) | `04_assembly_worker.webp` (40.3 KB) |
| **05** | **追因工** | `ROOTCAUSE_WORKER · TW-05` | 报表异常只是表象，顺着链路定位根因的是你。 | 【稳态·微趴型】身体压低前倾，手持强光探照手电筒与折线探针，挂 TW-05 工牌 | 探索深紫 (#8B5CF6) | `05_rootcause_worker.webp` (35.5 KB) |
| **06** | **守门工** | `GATEKEEPER_WORKER · TW-06` | 拦截隐患于发生之前，把关质量于交付之初。 | 【稳态·厚盾型】双手立着一面巨大半透明防爆闸门盾牌与重型金属铜锁，挂 TW-06 工牌 | 金属铜黄 (#F59E0B) | `06_gatekeeper_worker.webp` (40.0 KB) |
| **07** | **翻译工** | `TRANSLATOR_WORKER · TW-07` | 两边都说中文，但只有你能对上话。 | 【动态·灵巧型】头顶高敏接收双天线，手持双向翻转字典与双色对话对齐喇叭，挂 TW-07 工牌 | 双向暖金 (#F59E0B) | `07_translator_worker.webp` (44.5 KB) |
| **08** | **拆解工** | `DECONSTRUCTOR_WORKER · TW-08` | 别人给想法，你给可执行的清单。 | 【动态·修长爪】双手持发光大裁纸剪刀与锯齿标尺，整齐码放清单积木，挂 TW-08 工牌 | 警戒橙黄 (#EAB308) | `08_deconstructor_worker.webp` (39.0 KB) |
| **09** | **催办工** | `PROGRESS_WORKER · TW-09` | 所有人的延期，都会先出现在你的表格里。 | 【动态·大步奔跑】胸前挂大号倒计时秒表与催办进度条，大步向前冲刺飞奔，挂 TW-09 工牌 | 紧急亮黄 (#EAB308) | `09_progress_worker.webp` (59.0 KB) |
| **10** | **排雷工** | `MINESWEEPER_WORKER · TW-10` | 项目炸之前，只有你天天问“万一呢”。 | 【稳态·谨慎蹲踞】双手握长柄金属排雷探针，脚边插黄色警示三角旗，挂 TW-10 工牌 | 警示醒目黄 (#FACC15) | `10_minesweeper_worker.webp` (85.0 KB) |
| **11** | **解题工** | `SOLVER_WORKER · TW-11` | 客户的问题没有标准答案，你现场拼一个。 | 【动态·探头修长】双手托举悬浮立体变形魔方球，周围环绕几何微粒，挂 TW-11 工牌 | 数学薄荷蓝 (#2DD4BF) | `11_solver_worker.webp` (101.8 KB) |
| **12** | **应变工** | `ONSCENE_WORKER · TW-12` | 消息传到你这儿已经晚了十分钟，好在你人就在那儿。 | 【动态·前倾起跑】背负珊瑚红色多功能应急工具箱与对讲机天线，随时待命，挂 TW-12 工牌 | 急救珊瑚红 (#FB7185) | `12_onscene_worker.webp` (109.0 KB) |
| **00** | **神秘工 · 待解锁** | `SHADOW_WORKER · TW-00` | 证据不够，不下结论。 | 【未知态·半透明轮廓】暗哑炭黑短植绒质感，周身悬浮发光虚线环，挂醒目 TW-00 金色问号(?)工牌 | 发光亮黄 (#FDE047) | `00_shadow_worker.webp` (54.1 KB) |

### 5.3 全量 12+1 角色中文提示词规范与生图档案
- **底座风格与家族统领词 (通用前缀)**：
  `工牌绒绒家族角色，TW-XX[角色名]。摄影棚单色浅灰背景，正视全身像，潮玩手办雕像，精致短植绒毛材质。身体为中性冷灰色细密植绒，腹部米白。胸前挂带挂着写有TW-XX的白色小工牌。黑色哑光小圆豆眼，微露克制疲惫打工神态。手持[标志性道具]，辅助色为[专属辅助色]。没有大眼腮红，成年克制打工情绪，比例协调，纯净单色背景。`
- **体型骨架 6:6 平衡控制**：
  - **稳态 6 角色 (60%)**：TW-01(水桶墩)、TW-02(方块方墩)、TW-03(敦厚正圆)、TW-04(宽肩扎实)、TW-05(微趴低重心)、TW-06(厚盾圆柱)、TW-10(蹲踞扎稳)；
  - **动态 6 角色 (40%)**：TW-07(双天线前倾)、TW-08(修长爪步态)、TW-09(冲刺大步奔跑)、TW-11(修长探头托举)、TW-12(前倾应急起跑)；
  - **未知态 1 角色**：TW-00(暗黑炭灰绒毛剪影轮廓 + 发光亮黄问号工牌)。
- **原创避让**：全量角色不复刻任何既有商业 IP (Molly/Labubu/SKULLPANDA/BE@RBRICK)，以打工人真实职场疲态与极简几何绒毛为主体。

---

## 六、特殊状态与并存态呈现规范 (State Specifications)

根据冻结的内容基线规则（R4 双门槛语义），视觉层必须严格支持以下 3 种状态：

1. **标准态 (Normal State - 双门槛全过)**：
   - 显示真实指数数字（如 90）与等级标签（HIGH）；
   - 角色位陈列命中该案例的主角色（01~12 号透明素材）；
   - 展示角色专属正式昵称与金句嘴替。
2. **待解锁并存态 (Parallel State - 指数门槛过，但主角色门槛未过)**：
   - 指数位：**正常显示真数字**（按可判断任务计算得出的真实替代指数），绝不虚构、不隐藏；
   - 角色位：统一陈列 **`00_shadow_worker.webp`（神秘工立像）**；
   - 文案位：固定显示 **“证据不够，不下结论”**；**禁止随机分配角色，不显示角色昵称与角色介绍句**；
   - 嘴替句：从已判断任务的证据现写，但严禁暗示任何具体角色身份。
3. **完全不可判态 (Insufficient Info State - 双门槛均未过)**：
   - 指数位：不显示假分数，显示 `UNRATED` 或 `暂无指数`；
   - 角色位：展示 `00_shadow_worker.webp`，引导用户补充岗位任务描述与时间占比。

---

## 七、素材技术参数与实心抠图规范

- **格式标准**：WebP 格式（带 Alpha 透明通道），质量参数 q84，无损高保真；
- **画幅规格**：统一正方形 800 × 800 像素，主体比例占画布约 80%~85%，四周预留 8%~10% 安全留白；
- **实心防穿孔准则 (Anti-Punchthrough Algorithm)**：
  - 严禁单纯使用色彩欧氏距离全局抠图（避免白色肚皮、高光反光、工牌白底、浅色道具被抠穿）；
  - 采用**“低饱和度中性灰判别 + 外部 4 边界连通域单向 BFS 泛洪 + 高斯羽化抗锯齿”**算法，确保手办身体内部 100% 实心（Alpha = 255），外部摄影棚背景 100% 纯透明（Alpha = 0）；
- **体积指标**：13 张全量工牌绒绒实心 WebP 单张大小在 **34.1 KB ~ 109.0 KB** 之间，严格符合 ≤150KB 的工程硬约束；
- **存放路径**：
  - 设计小样目录：`visual_samples/characters/`
  - Skill 正式静态素材目录：`ai-task-exposure-skill/assets/characters/`

---

## 八、角色展示区底色物理隔离与展台规范 (Specimen Capsule System)

为彻底解决欧八提出的“透明素材导致海报背景颜色透出”问题，同时坚决避免将透明素材粗暴压死为单一固定底色而丧失复用能力，确立**“实体展示舱（Solid Specimen Capsule）+ 双层手办展台（Pedestal Base）”**的物理隔离方案：

### 8.1 视觉层级结构 (Layer Order)
1. **底层海报背景**：桌面端/移动端 `.stage-block`（亮黄色 `--c-yellow: #EBFB3B`）或微信分享卡全局黄色底板；
2. **实体展示仓背板 (Showcase Capsule)**：
   - 纯白色实心底（`#FFFFFF`），彻底在物理上阻绝外部海报黄底；
   - 粗黑边框：HTML 端 `3.5px solid #0D0D0D`，Canvas 端 5px 黑色边框；
   - 瑞士粗野主义硬圆角：HTML 端 `border-radius: 16px`，Canvas 端 `radius: 18px`；
   - 工业硬投影：HTML 端 `box-shadow: 6px 6px 0 var(--c-black)`，Canvas 端右下偏移硬黑投影；
3. **顶部标本标签条 (Specimen Ticker)**：
   - 仓内顶部嵌入浅灰（`#F4F4F0`）工程标签，单行显示 `SPECIMEN POD // SPECIMEN NO.XX · ROLE_CODE`，强化潮玩体检标本隐喻；
4. **实体手办台阶底座 (Pedestal Base)**：
   - 必须在手办脚底位置先行绘制（位于手办底层，严禁反客为主覆盖手办脚面）；
   - 下层宽黑椭圆托盘（厚度 24px~26px），上层深灰微反光台阶（`#2B2B2B`，厚度 16px~18px）；
5. **角色立像 (Solid Toy Specimen)**：
   - 居中稳稳立于展台之上，带有细腻的景深投影（`filter: drop-shadow(0 10px 18px rgba(0,0,0,.15))`），手办实体感十足。

### 8.2 Developer 落地代码规则参考

#### A. HTML / CSS 规则 (桌面端与移动端)
```css
/* 实体展示仓（纯白实心隔绝黄底） */
.character-stage {
  position: relative;
  width: 100%;
  margin: 14px 0;
  padding: 22px 16px 18px;
  background: var(--c-white);
  border: 3.5px solid var(--c-black);
  border-radius: 16px;
  box-shadow: 6px 6px 0 var(--c-black);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

/* 潮玩手办立像（层级 z-index: 2） */
.character-figure {
  position: relative;
  z-index: 2;
  width: min(380px, 100%);
  height: auto;
  display: block;
  filter: drop-shadow(0 10px 18px rgba(0, 0, 0, 0.15));
}

/* 实体展台底座（层级 z-index: 1，位于手办背后） */
.character-plinth {
  position: relative;
  z-index: 1;
  width: 68%;
  height: 22px;
  margin-top: -16px;
  background: radial-gradient(ellipse at center, #2b2b2b 0%, var(--c-black) 100%);
  border-radius: 50%;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.35);
}

/* 移动端 390 自适应紧凑适配 */
@media (max-width: 680px) {
  .character-stage {
    padding: 14px 10px 12px;
    margin: 8px 0;
    border-radius: 12px;
    box-shadow: 4px 4px 0 var(--c-black);
  }
  .character-figure { width: min(220px, 100%); }
  .character-plinth { width: 64%; height: 16px; margin-top: -12px; }
}
```

#### B. Canvas 微信分享卡 (1080×1440) 绘制规则
```javascript
if (image) {
  // 1. 实体展示仓右下硬投影 (x: 546, y: 102, w: 474, h: 504)
  roundedRect(546, 102, 474, 504, 18, BLACK, BLACK, 0);

  // 2. 纯白实心主体舱 (x: 540, y: 96, w: 474, h: 504, border: 5px)
  roundedRect(540, 96, 474, 504, 18, WHITE, BLACK, 5);

  // 3. 仓内顶部工程微标签条
  ctx.fillStyle = "#F4F4F0";
  ctx.fillRect(545, 101, 464, 36);
  ctx.fillStyle = BLACK;
  ctx.font = `700 15px ${mono}`;
  ctx.fillText(`SPECIMEN POD // ${specimen} · ${roleCode}`, 562, 125);

  // 4. 实体展台底座（脚底先行绘制：底层宽黑椭圆 + 上层灰台阶）
  ctx.fillStyle = BLACK;
  ctx.beginPath(); ctx.ellipse(777, 546, 175, 24, 0, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = "#2B2B2B";
  ctx.beginPath(); ctx.ellipse(777, 540, 145, 16, 0, 0, Math.PI * 2); ctx.fill();

  // 5. 居中绘制实心潮玩立像 (x: 557, y: 128, w: 440, h: 440)
  ctx.drawImage(image, 557, 128, 440, 440);
}
```

---
*本规范由视觉负责人（designer）制定，锁定 B 方向作为全量制作唯一视觉依据。*
