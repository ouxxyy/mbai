from copy import deepcopy


def valid_draft():
    draft = {
        "schema_version": "5.0.0",
        "rule_version": "5.0.0",
        "report_metadata": {
            "report_id": "fixture-project-owner",
            "generated_at": "2026-09-11T12:00:00+08:00",
            "confidence_level": "HIGH",
            "confidence_reason": "两项任务均有原文与责任边界证据。",
            "questions_asked": ["主要任务各占多少时间？", "哪些结果由你本人负责？"],
            "questions_skipped": False,
        },
        "source": {
            "input_type": "TEXT",
            "input_name": "fictional-resume.txt",
            "privacy_entities": ["张三", "星河科技", "江城大学", "阿波罗计划"],
            "extraction_status": "OK",
        },
        "profile": {
            "sanitized_category": "企业服务 / 项目交付",
            "role": {
                "code": "MINESWEEPER_WORKER",
                "reason": "承担上线风险取舍与客户解释，最贴近结果责任类。",
                "confidence": "HIGH",
                "name": "项目风险领航员",
                "tags": ["结果兜底", "跨团队协调"],
                "source_task_ids": ["task-weekly-report", "task-launch-decision"],
                "snarky_quote": "周报可以自动写，真正不能一键生成的是上线那晚谁来拍板。",
            },
        },
        "skill_panel": {
            "execution": {
                "score": 80,
                "evidence": "按周交付固定报告。",
                "is_known": True,
                "source_task_ids": ["task-weekly-report"],
            },
            "discretion": {
                "score": 90,
                "evidence": "根据上线风险决定是否延期。",
                "is_known": True,
                "source_task_ids": ["task-launch-decision"],
            },
            "coordination": {
                "score": 85,
                "evidence": "协调研发、销售与客户。",
                "is_known": True,
                "source_task_ids": ["task-launch-decision"],
            },
            "accountability": {
                "score": 90,
                "evidence": "承担上线结果与客户解释责任。",
                "is_known": True,
                "source_task_ids": ["task-launch-decision"],
            },
        },
        "tasks": [
            {
                "task_id": "task-weekly-report",
                "task_name": "汇总固定格式周报",
                "time_share_percent": 60,
                "exposure_level": "HIGH",
                "ai_can_do": "读取结构化数据并生成周报初稿。",
                "human_must_do": "核对异常数据并确认披露口径。",
                "evidence": "每周汇总渠道数据并输出固定模板周报。",
                "reason": "输入输出数字化且模板稳定，主体可自动完成。",
                "confidence": "HIGH",
                "signals": {
                    "judgment": 1,
                    "coordination": 0,
                    "physical_presence": 0,
                    "accountability": 1,
                    "repeatability": 2,
                    "digital_input_output": 2,
                },
            },
            {
                "task_id": "task-launch-decision",
                "task_name": "判断上线风险并协调各方",
                "time_share_percent": 40,
                "exposure_level": "LOW",
                "ai_can_do": "整理风险清单并模拟不同方案。",
                "human_must_do": "权衡客户影响并承担最终上线决策。",
                "evidence": "上线前组织评审，出现分歧时决定是否延期并向客户解释。",
                "reason": "核心是情境判断、多方协调和结果责任。",
                "confidence": "HIGH",
                "signals": {
                    "judgment": 2,
                    "coordination": 2,
                    "physical_presence": 0,
                    "accountability": 2,
                    "repeatability": 0,
                    "digital_input_output": 1,
                },
            },
        ],
        "human_edge": [
            {
                "summary": "能在上线风险、客户影响和交付承诺之间做取舍并承担结果。",
                "source_task_ids": ["task-launch-decision"],
            }
        ],
        "action_plan": {
            "hand_to_ai": {
                "title": "把周报初稿交给 AI",
                "action": "用脱敏数据生成固定模板周报初稿。",
                "deliverable": "一份自动生成的周报草稿和差异记录。",
                "acceptance_criteria": "连续两次生成，字段齐全且人工修订项少于五处。",
                "human_checkpoint": "发布前逐项核对异常值、业务口径和敏感数据。",
                "grounded_evidence": "当前每周执行固定格式汇总。",
                "source_task_ids": ["task-weekly-report"],
            },
            "level_up": {
                "title": "强化风险取舍记录",
                "action": "每次上线评审记录选项、代价、决定和事后结果。",
                "deliverable": "三张风险决策卡。",
                "acceptance_criteria": "每张均含至少两个备选方案和一次结果复盘。",
                "human_checkpoint": "只记录本人实际参与的判断，不补写未发生的成果。",
                "grounded_evidence": "已有上线拍板和客户解释经验。",
                "source_task_ids": ["task-launch-decision"],
            },
            "proof_7d": {
                "title": "做一份上线风险决策样例",
                "action": "用脱敏虚构案例重建一次上线取舍过程。",
                "deliverable": "两页 PDF 决策备忘录。",
                "acceptance_criteria": "包含背景、三项风险、两个方案、最终选择与验证指标。",
                "human_checkpoint": "移除客户、公司和项目标识后再对外展示。",
                "grounded_evidence": "源于真实的上线评审责任边界。",
                "source_task_ids": ["task-launch-decision"],
            },
        },
        "share_card": {
            "category": "企业服务 / 项目交付",
            "role_name": "项目风险领航员",
            "role_tags": ["结果兜底", "跨团队协调"],
            "confidence_label": "证据置信度：高",
            "irreplaceability_index": None,
            "irreplaceability_level": "UNKNOWN",
            "snarky_quote": "周报可以自动写，真正不能一键生成的是上线那晚谁来拍板。",
            "value_line": "我会协调各方，权衡客户影响，并承担上线取舍。",
            "source_task_ids": ["task-launch-decision"],
            "disclaimer": "本卡反映工作任务与 AI 能力的重合度，不是个人失业概率。",
        },
    }
    return deepcopy(draft)

