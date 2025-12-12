"""提示词配置中 docx 校验字段单元测试。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.service.prompt_config import parse_prompt_config


def test_docx_validation_enabled_requires_fonts_and_sizes() -> None:
    payload = {
        "system_prompt": "系统提示词",
        "categories": {
            "cat_a": {
                "display_name": "职业规划书",
                "docx_validation": {"enabled": True, "allowed_font_keywords": [], "allowed_font_size_pts": []},
                "sections": [
                    {
                        "key": "维度A",
                        "max_score": 1,
                        "items": [{"key": "细则A", "max_score": 1, "description": "描述"}],
                    }
                ],
            }
        },
    }
    with pytest.raises(ValueError):
        parse_prompt_config(payload)

