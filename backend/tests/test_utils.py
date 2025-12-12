"""工具函数单元测试。"""
from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.util.file_utils import extract_student_info, generate_batch_id


def test_generate_batch_id_format():
    batch_id = generate_batch_id()
    assert batch_id.startswith("batch-")
    parts = batch_id.split("-")
    assert len(parts) == 4
    assert len(parts[1]) == 8  # 日期部分
    assert len(parts[2]) == 6  # 时间部分
    assert len(parts[3]) == 6  # 随机串


def test_extract_student_info():
    student_id, student_name = extract_student_info("2023001_张三.docx")
    assert student_id == "2023001"
    assert student_name == "张三"
    sid2, sname2 = extract_student_info("不规则文件名.docx")
    assert sid2 is None
    assert sname2 is None
