"""作业分类识别逻辑单元测试。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.service import prompt_config as prompt_config_module
from app.service.rules import detect_assignment_category


def _write_min_prompt_config(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "system_prompt": "用于测试的系统提示词",
                "categories": {
                    "cat_a": {
                        "display_name": "职业规划书",
                        "sections": [
                            {
                                "key": "维度A",
                                "max_score": 1,
                                "items": [{"key": "细则A", "max_score": 1, "description": "描述"}],
                            }
                        ],
                    },
                    "cat_b": {
                        "display_name": "专业分析报告",
                        "sections": [
                            {
                                "key": "维度B",
                                "max_score": 1,
                                "items": [{"key": "细则B", "max_score": 1, "description": "描述"}],
                            }
                        ],
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_detect_assignment_category_auto_match(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "prompt_config.json"
    _write_min_prompt_config(config_path)
    monkeypatch.setattr(prompt_config_module, "PROMPT_CONFIG_PATH", config_path)

    assert detect_assignment_category("张三_职业规划书.txt", "auto") == "cat_a"
    assert detect_assignment_category("李四+专业分析报告.md", "auto") == "cat_b"


def test_detect_assignment_category_auto_conflict(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "prompt_config.json"
    _write_min_prompt_config(config_path)
    monkeypatch.setattr(prompt_config_module, "PROMPT_CONFIG_PATH", config_path)

    with pytest.raises(ValueError):
        detect_assignment_category("张三_职业规划书_专业分析报告.docx", "auto")


def test_detect_assignment_category_auto_no_match(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "prompt_config.json"
    _write_min_prompt_config(config_path)
    monkeypatch.setattr(prompt_config_module, "PROMPT_CONFIG_PATH", config_path)

    with pytest.raises(ValueError):
        detect_assignment_category("张三_作业一.txt", "auto")

