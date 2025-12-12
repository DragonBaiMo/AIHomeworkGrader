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
    docx_validation: "DocxValidationConfig"
    sections: List[PromptSection]


@dataclass(frozen=True)
class PromptConfig:
    """完整提示词配置。"""

    system_prompt: str
    categories: Dict[str, CategoryPromptConfig]


@dataclass(frozen=True)
class DocxValidationConfig:
    """docx 内部格式校验配置（不参与任何提示词构造与大模型输入）。"""

    enabled: bool
    allowed_font_keywords: List[str]
    allowed_font_size_pts: List[float]
    font_size_tolerance: float
    target_line_spacing: Optional[float]
    line_spacing_tolerance: Optional[float]


def _parse_docx_validation_config(raw: Any) -> DocxValidationConfig:
    if raw is None:
        return DocxValidationConfig(
            enabled=False,
            allowed_font_keywords=[],
            allowed_font_size_pts=[],
            font_size_tolerance=0.5,
            target_line_spacing=None,
            line_spacing_tolerance=None,
        )
    if not isinstance(raw, dict):
        raise ValueError("docx_validation 必须为对象")

    enabled = bool(raw.get("enabled") is True)
    allowed_fonts_raw = raw.get("allowed_font_keywords") or []
    allowed_sizes_raw = raw.get("allowed_font_size_pts") or []
    if not isinstance(allowed_fonts_raw, list) or any(not str(x).strip() for x in allowed_fonts_raw):
        raise ValueError("docx_validation.allowed_font_keywords 必须为字符串数组")
    if not isinstance(allowed_sizes_raw, list):
        raise ValueError("docx_validation.allowed_font_size_pts 必须为数字数组")

    allowed_font_keywords = [str(x).strip() for x in allowed_fonts_raw if str(x).strip()]
    allowed_font_size_pts: List[float] = []
    for x in allowed_sizes_raw:
        try:
            allowed_font_size_pts.append(float(x))
        except Exception as exc:  # noqa: BLE001
            raise ValueError("docx_validation.allowed_font_size_pts 必须为数字数组") from exc

    font_size_tolerance = float(raw.get("font_size_tolerance") or 0.5)
    if font_size_tolerance < 0:
        raise ValueError("docx_validation.font_size_tolerance 必须大于等于 0")

    target_line_spacing = raw.get("target_line_spacing")
    line_spacing_tolerance = raw.get("line_spacing_tolerance")
    target_line_spacing_f: Optional[float] = None
    line_spacing_tolerance_f: Optional[float] = None
    if target_line_spacing is not None or line_spacing_tolerance is not None:
        target_line_spacing_f = float(target_line_spacing or 0)
        line_spacing_tolerance_f = float(line_spacing_tolerance or 0.1)
        if target_line_spacing_f <= 0:
            raise ValueError("docx_validation.target_line_spacing 必须大于 0")
        if line_spacing_tolerance_f < 0:
            raise ValueError("docx_validation.line_spacing_tolerance 必须大于等于 0")

    if enabled:
        if not allowed_font_keywords:
            raise ValueError("docx_validation 已启用，但未配置 allowed_font_keywords")
        if not allowed_font_size_pts:
            raise ValueError("docx_validation 已启用，但未配置 allowed_font_size_pts")
        if any(v <= 0 for v in allowed_font_size_pts):
            raise ValueError("docx_validation.allowed_font_size_pts 必须全部大于 0")

    return DocxValidationConfig(
        enabled=enabled,
        allowed_font_keywords=allowed_font_keywords,
        allowed_font_size_pts=allowed_font_size_pts,
        font_size_tolerance=font_size_tolerance,
        target_line_spacing=target_line_spacing_f,
        line_spacing_tolerance=line_spacing_tolerance_f,
    )


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
        docx_validation = _parse_docx_validation_config(cat_value.get("docx_validation"))
        raw_sections = cat_value.get("sections")
        if not isinstance(raw_sections, list) or not raw_sections:
            raise ValueError(f"categories.{cat_key}.sections 不能为空")
        sections: List[PromptSection] = []
        section_names: set[str] = set()
        for sec in raw_sections:
            if not isinstance(sec, dict):
                raise ValueError(f"categories.{cat_key}.sections 条目必须为对象")
            sec_key = str(sec.get("key") or "").strip()
            if not sec_key:
                raise ValueError(f"categories.{cat_key}.sections.key 不能为空")
            if sec_key in section_names:
                raise ValueError(f"categories.{cat_key}.sections 存在重复维度名称：{sec_key}")
            section_names.add(sec_key)
            raw_items = sec.get("items")
            if not isinstance(raw_items, list) or not raw_items:
                raise ValueError(f"categories.{cat_key}.sections[{sec_key}].items 不能为空")
            items: List[PromptItem] = []
            item_names: set[str] = set()
            items_sum = 0.0
            for item in raw_items:
                if not isinstance(item, dict):
                    raise ValueError(f"categories.{cat_key}.sections[{sec_key}].items 条目必须为对象")
                item_key = str(item.get("key") or "").strip()
                item_max = float(item.get("max_score") or 0)
                item_desc = str(item.get("description") or "").strip()
                if not item_key:
                    raise ValueError(f"categories.{cat_key}.sections[{sec_key}].items.key 不能为空")
                if item_key in item_names:
                    raise ValueError(f"categories.{cat_key}.sections[{sec_key}].items 存在重复细则名称：{item_key}")
                item_names.add(item_key)
                if item_max <= 0 or not item_desc:
                    raise ValueError(f"categories.{cat_key}.sections[{sec_key}].items.key/max_score/description 非法")
                items.append(PromptItem(key=item_key, max_score=item_max, description=item_desc))
                items_sum += float(item_max)

            # 兼容旧配置：若维度 max_score 与细则求和不一致，自动以细则求和为准，并记录日志。
            sec_max_raw = float(sec.get("max_score") or 0)
            if sec_max_raw > 0 and abs(sec_max_raw - items_sum) > 1e-6:
                logger.warning("评分维度“%s”满分与细则求和不一致：维度=%s，细则求和=%s，已自动更正为细则求和。", sec_key, sec_max_raw, items_sum)
            sections.append(PromptSection(key=sec_key, max_score=items_sum, items=items))
        categories[str(cat_key)] = CategoryPromptConfig(display_name=display_name, docx_validation=docx_validation, sections=sections)

    return PromptConfig(system_prompt=system_prompt, categories=categories)


def save_prompt_config(data: Dict[str, Any]) -> PromptConfig:
    """保存提示词配置并同步生成 prompts.md。"""
    config = parse_prompt_config(data)

    # 归一化：将维度 max_score 自动同步为细则求和，避免前端误填导致逻辑歧义。
    normalized: Dict[str, Any] = json.loads(json.dumps(data, ensure_ascii=False))
    for cat_value in (normalized.get("categories") or {}).values():
        if not isinstance(cat_value, dict):
            continue
        # 归一化 docx 校验配置默认值，便于后端稳定读取。
        if "docx_validation" not in cat_value or cat_value.get("docx_validation") is None:
            cat_value["docx_validation"] = {
                "enabled": False,
                "allowed_font_keywords": [],
                "allowed_font_size_pts": [],
                "font_size_tolerance": 0.5,
            }
        sections = cat_value.get("sections")
        if not isinstance(sections, list):
            continue
        for sec in sections:
            if not isinstance(sec, dict):
                continue
            items = sec.get("items")
            if not isinstance(items, list):
                continue
            sec["max_score"] = float(sum(float((i or {}).get("max_score") or 0) for i in items))

    PROMPT_CONFIG_PATH.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
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
    parts.append(f"你是一名高校教师，请严格依据评分标准批改学生的《{cat_cfg.display_name}》。")
    parts.append("评分标准来自系统配置，请逐条细则给分，并说明扣分原因。")
    parts.append("")
    for idx, sec in enumerate(cat_cfg.sections, start=1):
        parts.append(f"{idx}、{sec.key}（{sec.max_score}分）")
        for item_idx, item in enumerate(sec.items, start=1):
            parts.append(f"{item_idx}. {item.key}（{item.max_score}分）：{item.description}")
        parts.append("")
    parts.append("【学生作业正文】")
    parts.append("{{HOMEWORK_TEXT}}")
    return "\n".join(parts).strip()
