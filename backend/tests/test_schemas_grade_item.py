"""接口数据模型单元测试。"""
from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.model.schemas import GradeItem


def test_grade_item_raw_response_default_none() -> None:
    item = GradeItem(
        file_name="张三_职业规划书.docx",
        student_id=None,
        student_name=None,
        score=None,
        score_rubric_max=None,
        score_rubric=None,
        detail_json=None,
        comment=None,
        status="失败",
        error_message="解析失败",
        raw_text_length=0,
    )
    assert item.raw_response is None

