"""
提示词编译模块（低代码核心）。

目标：
1) 由前端评分维度配置动态生成 User Prompt；
2) 在 System Prompt 中强制约束输出为 schema_version=2 的 JSON；
3) 支持“规则总分 -> 目标满分”的按比例换算。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List

from app.service.prompt_config import (
    CategoryPromptConfig,
    RUBRIC_SYSTEM_HARD_RULES_KEY,
    RUBRIC_USER_TEMPLATE_KEY,
    default_rubric_system_hard_rules,
    default_rubric_user_template,
    load_prompts_md_sections,
    is_placeholder_text,
)


@dataclass(frozen=True)
class RubricItem:
    """评分细则定义（用于校验模型输出对齐）。"""

    name: str
    max_score: float


@dataclass(frozen=True)
class RubricSection:
    """评分维度定义（用于校验模型输出对齐）。"""

    name: str
    max_score: float
    items: List[RubricItem]


@dataclass(frozen=True)
class RubricExpected:
    """本次评分所期望的评分结构。"""

    category_name: str
    rubric_max: float
    sections: List[RubricSection]


def build_system_prompt(base_system_prompt: str) -> str:
    """构造最终 System Prompt（在用户配置基础上强制追加硬性规范）。"""
    base = (base_system_prompt or "").strip()
    if not base:
        base = "你是一名严格的高校教师，负责批改学生作业。"
    md_sections = load_prompts_md_sections()
    hard_rules = (md_sections.get(RUBRIC_SYSTEM_HARD_RULES_KEY) or "").strip() or default_rubric_system_hard_rules()
    return f"{base}\n\n{hard_rules}".strip()


def build_expected_rubric(category_cfg: CategoryPromptConfig) -> RubricExpected:
    """从分类配置构造期望的评分结构。"""
    sections: List[RubricSection] = []
    total = 0.0
    for sec in category_cfg.sections:
        items: List[RubricItem] = []
        sec_sum = 0.0
        for item in sec.items:
            items.append(RubricItem(name=item.key, max_score=float(item.max_score)))
            sec_sum += float(item.max_score)
        sections.append(RubricSection(name=sec.key, max_score=sec_sum, items=items))
        total += sec_sum
    return RubricExpected(category_name=category_cfg.display_name, rubric_max=total, sections=sections)


def _render_rubric_human_text(category_cfg: CategoryPromptConfig) -> str:
    lines: List[str] = []
    lines.append(f"- category_name：{category_cfg.display_name}")
    lines.append(" - rubric：")
    for idx, sec in enumerate(category_cfg.sections, start=1):
        sec_total = sum(float(i.max_score) for i in sec.items)
        lines.append(f"   {idx}、{sec.key}（{sec_total}分）")
        for item_idx, item in enumerate(sec.items, start=1):
            lines.append(f"   {item_idx}. {item.key}（{float(item.max_score)}分）：{item.description}")
    return "\n".join(lines).strip()


def _render_output_skeleton(expected: RubricExpected, score_target_max: float) -> Dict[str, Any]:
    sections_out: List[Dict[str, Any]] = []
    for sec in expected.sections:
        items_out: List[Dict[str, Any]] = []
        for item in sec.items:
            items_out.append(
                {
                    "name": item.name,
                    "score": None,
                    "comment": "（占位符：请填写该细则的扣分原因或得分依据）",
                }
            )
        sections_out.append(
            {
                "name": sec.name,
                "comment": "（占位符：请填写该维度的总体评价）",
                "items": items_out,
            }
        )
    return {
        "schema_version": 2,
        "category_name": expected.category_name,
        "comment": "（占位符：请填写总体评语，中文≤150字）",
        "sections": sections_out,
    }


def build_user_prompt(category_cfg: CategoryPromptConfig, score_target_max: float, category_key: str | None = None) -> tuple[str, RubricExpected]:
    """构造最终 User Prompt（包含评分配置 + 输出骨架 + 作业正文占位符）。"""
    expected = build_expected_rubric(category_cfg)
    skeleton = _render_output_skeleton(expected, score_target_max)
    skeleton_text = json.dumps(skeleton, ensure_ascii=False, indent=2)
    rubric_text = _render_rubric_human_text(category_cfg)
    user_prompt = build_user_prompt_from_template(
        rubric_text=rubric_text,
        output_skeleton_json=skeleton_text,
        homework_text_placeholder="{{HOMEWORK_TEXT}}",
        category_key=category_key,
    )
    return user_prompt, expected


def build_user_prompt_from_template(*, rubric_text: str, output_skeleton_json: str, homework_text_placeholder: str, category_key: str | None = None) -> str:
    """从 prompts.md 的模板段落构造 User Prompt（便于可编辑与测试）。"""
    md_sections = load_prompts_md_sections()
    
    # 优先查找分类特定的模板（如果存在且不是占位符）
    template: str | None = None
    if category_key:
        specific = (md_sections.get(category_key) or "").strip()
        if specific and not is_placeholder_text(specific):
            template = specific
    
    # 否则使用全局模板
    if not template:
        template = (md_sections.get(RUBRIC_USER_TEMPLATE_KEY) or "").strip() or default_rubric_user_template()
        
    return (
        template.replace("{{RUBRIC_HUMAN_TEXT}}", str(rubric_text))
        .replace("{{OUTPUT_SKELETON_JSON}}", str(output_skeleton_json))
        .replace("{{HOMEWORK_TEXT}}", str(homework_text_placeholder))
        .strip()
    )
