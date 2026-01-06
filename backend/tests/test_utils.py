"""工具函数单元测试。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.util.file_utils import extract_student_info, generate_batch_id, parse_filename_meta
from app.util.files.constants import STUDENT_ID_REGEX, TITLE_KEYWORDS


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


def _parse_md_listing_names(lines: list[str]) -> list[str]:
    names: list[str] = []
    for line in lines:
        if not line.strip() or line.startswith("Mode ") or line.startswith("----"):
            continue
        tokens = line.split()
        if len(tokens) < 4:
            continue
        name = " ".join(tokens[3:])
        if name:
            names.append(name)
    return names


def test_filename_md_samples_have_student_id_when_present():
    md_path = BASE_DIR.parent / "同学的文件名.md"
    lines = md_path.read_text(encoding="utf-8").splitlines()
    for name in _parse_md_listing_names(lines):
        expected_ids = re.findall(STUDENT_ID_REGEX, name)
        meta = parse_filename_meta(name)
        if not expected_ids:
            assert meta.student_id is None
            continue
        assert meta.student_id in expected_ids
        assert re.fullmatch(STUDENT_ID_REGEX, meta.student_id)


def test_filename_md_samples_title_normalized():
    md_path = BASE_DIR.parent / "同学的文件名.md"
    lines = md_path.read_text(encoding="utf-8").splitlines()
    for name in _parse_md_listing_names(lines):
        meta = parse_filename_meta(name)
        if meta.assignment_title is None:
            continue
        assert meta.assignment_title in TITLE_KEYWORDS


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

    meta6 = parse_filename_meta("14:59 24050 25物联网工程2班  胡伟迪 202502210118  专业分析报告.docx")
    assert meta6.student_id == "202502210118"
    assert meta6.student_name == "胡伟迪"
    assert meta6.class_name == "25物联网工程2班"

    meta7 = parse_filename_meta("25物联网工程2班吴梓丹202502210217专业分析作业.docx")
    assert meta7.student_id == "202502210217"
    assert meta7.student_name == "吴梓丹"

    meta8 = parse_filename_meta("25通信工程1班（华为5G创新班）202502210046邱耀霆 专业分析报告.docx")
    assert meta8.student_id == "202502210046"
    assert meta8.student_name == "邱耀霆"

    meta9 = parse_filename_meta("25通信工程一班+202502210039+邱君皓+专业分析报告.docx")
    assert meta9.student_id == "202502210039"
    assert meta9.student_name == "邱君皓"

    meta10 = parse_filename_meta("职业规划书作业25通信工程一班陈昱昊202502210022.docx")
    assert meta10.student_id == "202502210022"
    assert meta10.student_name == "陈昱昊"

    meta11 = parse_filename_meta("专业分析报告韦诗蕴202502210321.docx")
    assert meta11.student_id == "202502210321"
    assert meta11.student_name == "韦诗蕴"

    meta12 = parse_filename_meta("25物联网工程2班 康清彦202502210106 专业分析报告.docx")
    assert meta12.student_id == "202502210106"
    assert meta12.student_name == "康清彦"
    assert meta12.class_name == "25物联网工程2班"

    meta13 = parse_filename_meta("25物联网工程2班202502210154甘昶博专业分析报告.docx")
    assert meta13.student_id == "202502210154"
    assert meta13.student_name == "甘昶博"
    assert meta13.class_name == "25物联网工程2班"

    meta14 = parse_filename_meta("25物联网工程2班的谭怡然202502210187专业分析报告·.docx")
    assert meta14.student_id == "202502210187"
    assert meta14.student_name == "谭怡然"
    assert meta14.class_name == "25物联网工程2班"

    meta15 = parse_filename_meta("202502210373     李永浩   职业规划书.docx")
    assert meta15.student_id == "202502210373"
    assert meta15.student_name == "李永浩"

    meta16 = parse_filename_meta("25计科2班（华为ICT） 江嘉华  202502210344 专业分析报告.docx")
    assert meta16.student_id == "202502210344"
    assert meta16.student_name == "江嘉华"
    assert meta16.class_name == "25计科2班"

    meta17 = parse_filename_meta("25物联网工程3班-唐琨博-202502210207.docx")
    assert meta17.student_id == "202502210207"
    assert meta17.student_name == "唐琨博"

    meta18 = parse_filename_meta("25物联网工程三班利焘20250221013专业分析报告.docx")
    assert meta18.student_id == "20250221013"
    assert meta18.student_name == "利焘"
    assert meta18.assignment_title == "专业分析报告"

    meta19 = parse_filename_meta("25物联网工程3班余华宇202502210193专业认知报告分析.docx")
    assert meta19.student_id == "202502210193"
    assert meta19.student_name == "余华宇"
    assert meta19.assignment_title == "专业认知报告"

    meta20 = parse_filename_meta("25物联网工程3班+刘依键+202502210087+专业分析报告(1).docx")
    assert meta20.student_id == "202502210087"
    assert meta20.student_name == "刘依键"
    assert meta20.assignment_title == "专业分析报告"

    meta21 = parse_filename_meta("25物联网工程三班-苏勇-202502210161-专业分析报告.docx")
    assert meta21.student_id == "202502210161"
    assert meta21.student_name == "苏勇"
    assert meta21.assignment_title == "专业分析报告"

    meta22 = parse_filename_meta("25 物联网工程 3 班 成国邦 202502210209 职业规划书作业模板.docx")
    assert meta22.student_id == "202502210209"
    assert meta22.student_name == "成国邦"
    assert meta22.assignment_title == "职业规划书"

    meta23 = parse_filename_meta("25物联网工程·3班干乐怡202502210407职业规划书.docx")
    assert meta23.student_id == "202502210407"
    assert meta23.student_name == "干乐怡"
    assert meta23.assignment_title == "职业规划书"

    meta24 = parse_filename_meta("25计科2班黄鑫华202502210310游戏开发师职业规划.docx")
    assert meta24.student_id == "202502210310"
    assert meta24.student_name == "黄鑫华"
    assert meta24.assignment_title == "职业规划"

    meta25 = parse_filename_meta("《专业分析报告》 戴楚浩  202502210247.docx")
    assert meta25.student_id == "202502210247"
    assert meta25.student_name == "戴楚浩"
    assert meta25.assignment_title == "专业分析报告"

    meta26 = parse_filename_meta("华为ICT计科2班 郭泓成 202502210400 《专业分析报告》.docx")
    assert meta26.student_id == "202502210400"
    assert meta26.student_name == "郭泓成"
    assert meta26.assignment_title == "专业分析报告"

    meta27 = parse_filename_meta("职业规划书-王明栋-202502210230-华为计算机科学与技术2班.docx")
    assert meta27.student_id == "202502210230"
    assert meta27.student_name == "王明栋"
    assert meta27.assignment_title == "职业规划书"

    meta28 = parse_filename_meta("25通信工程1班 王月淏 202502210052. 通信工程专业分析报告docx.docx")
    assert meta28.student_id == "202502210052"
    assert meta28.student_name == "王月淏"
    assert meta28.assignment_title == "专业分析报告"

    meta29 = parse_filename_meta("25通信工程一班专业分析作业202502210056邱梓铭(.docx")
    assert meta29.student_id == "202502210056"
    assert meta29.student_name == "邱梓铭"
    assert meta29.assignment_title == "专业分析作业"

    meta30 = parse_filename_meta("[通信工程一班 朱含笙 202502210008 专业分析导论(1)(1).docx")
    assert meta30.student_id == "202502210008"
    assert meta30.student_name == "朱含笙"
    assert meta30.assignment_title == "专业分析导论"

    meta31 = parse_filename_meta("202502210045吴漠洲25通信工程一班职业规划.doc")
    assert meta31.student_id == "202502210045"
    assert meta31.student_name == "吴漠洲"
    assert meta31.assignment_title == "职业规划"

    meta32 = parse_filename_meta("25计算机科学与技术2班（华为鲲鹏云创新班）202502210376张宇彤职业规划书.docx")
    assert meta32.student_id == "202502210376"
    assert meta32.student_name == "张宇彤"
    assert meta32.assignment_title == "职业规划书"

    meta33 = parse_filename_meta("罗倩怡_202502210340_职业规划书.docx")
    assert meta33.student_id == "202502210340"
    assert meta33.student_name == "罗倩怡"
    assert meta33.assignment_title == "职业规划书"

    meta34 = parse_filename_meta("李文豪职业规划书.doc")
    assert meta34.student_id is None
    assert meta34.student_name is None

    meta35 = parse_filename_meta("25物联网工程3班 庞俊鸿 202502210206(1).docx")
    assert meta35.student_id == "202502210206"
    assert meta35.student_name == "庞俊鸿"
