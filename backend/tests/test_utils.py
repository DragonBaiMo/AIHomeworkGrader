"""工具函数单元测试。"""
from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.util.file_utils import extract_student_info, generate_batch_id, parse_filename_meta


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


def test_parse_filename_meta_common_formats():
    meta = parse_filename_meta("25计算机科学与技术1班+张三三+202502210111+职业规划书.docx")
    assert meta.class_name == "25计算机科学与技术1班"
    assert meta.student_name == "张三三"
    assert meta.student_id == "202502210111"
    assert meta.assignment_title == "职业规划书"

    meta2 = parse_filename_meta("25计算机科学与技术1班-张三三-202502210111-专业分析报告.docx")
    assert meta2.student_id == "202502210111"
    assert meta2.student_name == "张三三"

    meta3 = parse_filename_meta("【25计算机科学与技术1班】张三三【202502210111】专业分析报告.docx")
    assert meta3.student_id == "202502210111"
    assert meta3.student_name == "张三三"
    assert meta3.assignment_title == "专业分析报告"

    meta4 = parse_filename_meta("班级=25计算机科学与技术1班_姓名=张三三_学号=202502210111_作业=专业分析报告.docx")
    assert meta4.student_id == "202502210111"
    assert meta4.student_name == "张三三"

    meta5 = parse_filename_meta("25计算机科学与技术1班张三三202502210111专业分析报告.docx")
    assert meta5.student_id == "202502210111"
    assert meta5.assignment_title == "专业分析报告"
