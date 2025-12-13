"""prompts.md 渲染占位符与可编辑段落测试。"""
from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.service.prompt_config import OVERALL_COMMENT_SYSTEM_KEY, OVERALL_COMMENT_USER_KEY, RUBRIC_SYSTEM_HARD_RULES_KEY, RUBRIC_USER_TEMPLATE_KEY, PromptConfig, CategoryPromptConfig, DocxValidationConfig, PromptSection, PromptItem, render_prompts_md


def test_render_prompts_md_contains_placeholders_for_categories() -> None:
    cfg = PromptConfig(
        system_prompt="系统提示词",
        categories={
            "cat_a": CategoryPromptConfig(
                display_name="A类作业",
                docx_validation=DocxValidationConfig(
                    enabled=False,
                    allowed_font_keywords=[],
                    allowed_font_size_pts=[],
                    font_size_tolerance=0.5,
                    target_line_spacing=None,
                    line_spacing_tolerance=None,
                ),
                sections=[PromptSection(key="维度", max_score=1.0, items=[PromptItem(key="细则", max_score=1.0, description="描述")])],
            )
        },
    )
    text = render_prompts_md(cfg, existing_sections={})
    assert "## system" in text
    assert f"## {OVERALL_COMMENT_SYSTEM_KEY}" in text
    assert f"## {OVERALL_COMMENT_USER_KEY}" in text
    assert f"## {RUBRIC_SYSTEM_HARD_RULES_KEY}" in text
    assert f"## {RUBRIC_USER_TEMPLATE_KEY}" in text
    assert "## cat_a" in text
    assert "（占位符：" in text
