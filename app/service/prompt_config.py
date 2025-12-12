"""
评分提示词配置管理模块。

提供提示词 JSON 配置的读取、校验、保存，以及根据配置生成 prompts.md。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import BASE_DIR
from app.util.logger import logger

PROMPT_CONFIG_PATH = BASE_DIR / "config" / "prompt_config.json"
PROMPT_MD_PATH = BASE_DIR / "config" / "prompts.md"


@dataclass(frozen=True)
class PromptItem:
    """评分细项配置。"""

    key: str
    max_score: float
    description: str


@dataclass(frozen=True)
class PromptSection:
    """评分大项配置。"""

    key: str
    max_score: float
    items: List[PromptItem]


@dataclass(frozen=True)
class CategoryPromptConfig:
    """单类作业的评分提示词配置。"""

    display_name: str
    sections: List[PromptSection]


@dataclass(frozen=True)
class PromptConfig:
    """完整提示词配置。"""

    system_prompt: str
    categories: Dict[str, CategoryPromptConfig]


def load_prompt_config() -> Optional[PromptConfig]:
    """读取提示词 JSON 配置，不存在则返回 None。"""
    if not PROMPT_CONFIG_PATH.exists():
        return None
    try:
        data = json.loads(PROMPT_CONFIG_PATH.read_text(encoding="utf-8"))
        return parse_prompt_config(data)
    except Exception as exc:  # noqa: BLE001
        logger.error("读取提示词配置失败：%s", exc)
        return None


def parse_prompt_config(data: Dict[str, Any]) -> PromptConfig:
    """校验并解析提示词配置字典。"""
    if not isinstance(data, dict):
        raise ValueError("提示词配置必须为对象")

    system_prompt = str(data.get("system_prompt") or "").strip()
    if not system_prompt:
        raise ValueError("system_prompt 不能为空")

    raw_categories = data.get("categories")
    if not isinstance(raw_categories, dict) or not raw_categories:
        raise ValueError("categories 不能为空")

    categories: Dict[str, CategoryPromptConfig] = {}
    for cat_key, cat_value in raw_categories.items():
        if not isinstance(cat_value, dict):
            raise ValueError(f"categories.{cat_key} 必须为对象")
        display_name = str(cat_value.get("display_name") or "").strip()
        if not display_name:
            raise ValueError(f"categories.{cat_key}.display_name 不能为空")
        raw_sections = cat_value.get("sections")
        if not isinstance(raw_sections, list) or not raw_sections:
            raise ValueError(f"categories.{cat_key}.sections 不能为空")
        sections: List[PromptSection] = []
        for sec in raw_sections:
            if not isinstance(sec, dict):
                raise ValueError(f"categories.{cat_key}.sections 条目必须为对象")
            sec_key = str(sec.get("key") or "").strip()
            sec_max = float(sec.get("max_score") or 0)
            if not sec_key or sec_max <= 0:
                raise ValueError(f"categories.{cat_key}.sections.key/max_score 非法")
            raw_items = sec.get("items")
            if not isinstance(raw_items, list) or not raw_items:
                raise ValueError(f"categories.{cat_key}.sections[{sec_key}].items 不能为空")
            items: List[PromptItem] = []
            for item in raw_items:
                if not isinstance(item, dict):
                    raise ValueError(f"categories.{cat_key}.sections[{sec_key}].items 条目必须为对象")
                item_key = str(item.get("key") or "").strip()
                item_max = float(item.get("max_score") or 0)
                item_desc = str(item.get("description") or "").strip()
                if not item_key or item_max <= 0 or not item_desc:
                    raise ValueError(f"categories.{cat_key}.sections[{sec_key}].items.key/max_score/description 非法")
                items.append(PromptItem(key=item_key, max_score=item_max, description=item_desc))
            sections.append(PromptSection(key=sec_key, max_score=sec_max, items=items))
        categories[str(cat_key)] = CategoryPromptConfig(display_name=display_name, sections=sections)

    return PromptConfig(system_prompt=system_prompt, categories=categories)


def save_prompt_config(data: Dict[str, Any]) -> PromptConfig:
    """保存提示词配置并同步生成 prompts.md。"""
    config = parse_prompt_config(data)
    PROMPT_CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    md_text = render_prompts_md(config)
    PROMPT_MD_PATH.write_text(md_text, encoding="utf-8")
    logger.info("提示词配置已保存并同步至 prompts.md")
    return config


def render_prompts_md(config: PromptConfig) -> str:
    """根据配置渲染 prompts.md 内容。"""
    lines: List[str] = []
    lines.append("# 大模型提示词配置（自动生成）")
    lines.append("")
    lines.append("## system")
    lines.append(config.system_prompt.strip())
    lines.append("")
    for cat_key, cat_cfg in config.categories.items():
        lines.append(f"## {cat_key}")
        lines.append(render_category_prompt(cat_cfg))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_category_prompt(cat_cfg: CategoryPromptConfig) -> str:
    """渲染单类作业的评分提示词正文（User Prompt）。"""
    parts: List[str] = []
    parts.append(f"你是一名高校教师，请严格依据以下评分标准批改学生的《{cat_cfg.display_name}》，满分 100 分。")
    parts.append("请逐项对照评分点给分，并在评语中说明扣分原因。")
    parts.append("总分必须为所有细项得分之和，不得凭印象随意估分。")
    parts.append("")

    for idx, sec in enumerate(cat_cfg.sections, start=1):
        parts.append(f"{idx}、{sec.key}（{sec.max_score}分）")
        for item_idx, item in enumerate(sec.items, start=1):
            parts.append(f"{item_idx}. {item.key}（{item.max_score}分）：{item.description}")
        parts.append("")

    parts.append("【学生作业正文】")
    parts.append("{{HOMEWORK_TEXT}}")
    return "\n".join(parts).strip()

