"""文件元信息解析，负责文件名拆解与识别。"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from app.util.files.constants import FILENAME_FORMAT_HINT
from app.util.logger import logger


@dataclass
class FileMeta:
    """从文件名中解析出的基础元信息。"""

    original_name: str
    class_name: Optional[str]
    student_name: Optional[str]
    student_id: Optional[str]
    assignment_title: Optional[str]


def extract_student_info(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    兼容旧逻辑：仅返回学号与姓名。

    优先按“班级+姓名+学号+作业名称”格式解析，无法识别时退回简单分隔规则。
    """
    meta = parse_filename_meta(filename)
    if meta.student_id or meta.student_name:
        return meta.student_id, meta.student_name

    stem = Path(filename).stem
    if "_" in stem:
        student_id, student_name = stem.split("_", 1)
        return student_id.strip(), student_name.strip()
    if "-" in stem:
        student_id, student_name = stem.split("-", 1)
        return student_id.strip(), student_name.strip()
    return None, None


def parse_filename_meta(filename: str) -> FileMeta:
    """
    解析文件名中的班级、姓名、学号与作业名称。

    规范格式示例：
    25计算机科学与技术1班+张三三+202502210111+职业规划书.docx
    """
    stem = Path(filename).stem.strip()

    def normalize_text(text: str) -> str:
        return (
            text.replace("｜", "|")
            .replace("‖", "|")
            .replace("·", ".")
            .replace("—", "-")
            .replace("–", "-")
            .strip()
        )

    stem_norm = normalize_text(stem)

    def clean_token(token: str) -> str:
        t = token.strip()
        # 去掉常见外壳
        t = re.sub(r"^[【\[\(（]+|[】\]\)）]+$", "", t).strip()
        # 去掉前缀噪音
        t = re.sub(r"^(作业提交|作业|Homework|HOMEWORK|作业_提交)[:：_\-]*", "", t).strip()
        return t

    # 1) 键值对格式：班级=... 姓名=... 学号=... 作业=...
    kv_patterns = {
        "class_name": r"(?:班级|Class|CLASS)",
        "student_name": r"(?:姓名|Name|NAME)",
        "student_id": r"(?:学号|ID|Id|id)",
        "assignment_title": r"(?:作业|Work|WORK|Assignment|ASSIGNMENT)",
    }
    kv_found: dict[str, str] = {}
    for field, key_pat in kv_patterns.items():
        m = re.search(rf"{key_pat}\s*[:=－\-]\s*([^_\-+@|.]+)", stem_norm)
        if m:
            kv_found[field] = clean_token(m.group(1))
    if kv_found.get("student_id") and kv_found.get("student_name"):
        return FileMeta(
            original_name=filename,
            class_name=kv_found.get("class_name") or None,
            student_name=kv_found.get("student_name") or None,
            student_id=kv_found.get("student_id") or None,
            assignment_title=kv_found.get("assignment_title") or None,
        )

    # 2) 统一分隔符切分（支持 + _ - | . @ 空格）
    tokens = [clean_token(t) for t in re.split(r"[+_\-@|.\s]+", stem_norm) if clean_token(t)]

    # 3) 补充“【...】...”这种：将括号内也当作 token
    bracket_tokens = [clean_token(t) for t in re.findall(r"[【\[\(（]([^【\]\)）]+)[】\]\)）]", stem_norm)]
    for bt in bracket_tokens:
        if bt and bt not in tokens:
            tokens.insert(0, bt)

    def guess_student_id(text: str) -> Optional[str]:
        # 学号通常为 6-20 位纯数字
        candidates = re.findall(r"\d{6,20}", text)
        if not candidates:
            return None
        # 取最长的那一个
        return sorted(candidates, key=len, reverse=True)[0]

    def is_class_token(t: str) -> bool:
        return ("班" in t) or re.search(r"\bclass\b", t, flags=re.IGNORECASE) is not None

    def is_name_token(t: str) -> bool:
        # 允许中文姓名、拼音/英文名
        if re.fullmatch(r"[\u4e00-\u9fff·•]{2,10}", t):
            return True
        if re.fullmatch(r"[A-Za-z][A-Za-z.\-]{1,30}", t):
            return True
        return False

    student_id = guess_student_id(stem_norm)
    class_name: Optional[str] = None
    student_name: Optional[str] = None
    assignment_title: Optional[str] = None

    # 4) 从 tokens 中推断字段
    for t in tokens:
        if not t:
            continue
        if student_id is None:
            sid = guess_student_id(t)
            if sid:
                student_id = sid
                continue
        if class_name is None and is_class_token(t):
            class_name = t
            continue
        if student_name is None and is_name_token(t) and (student_id is None or student_id not in t):
            # 避免将任意中文短语误判为姓名：若未识别到学号，则仅在已识别到班级时才接受姓名。
            if student_id is None and class_name is None:
                continue
            student_name = t
            continue

    # 5) 作业名称：尽量取最后一个“不像班级/姓名/学号”的 token
    reserved = set(filter(None, [class_name, student_name, student_id]))
    for t in reversed(tokens):
        if t and t not in reserved:
            assignment_title = t
            break

    # 6) 处理“单 token 但其实是无分隔符拼接”的情况
    if len(tokens) == 1 and student_id and ("班" in stem_norm):
        tokens = []

    # 7) 极端无分隔符：25计科1班张三三202502210111专业分析报告
    if not tokens and (student_id or ("班" in stem_norm)):
        if student_id:
            left, right = stem_norm.split(student_id, 1)
            # 从左边找班级
            m_class = re.search(r"(.+?班)", left)
            if m_class:
                class_name = clean_token(m_class.group(1))
            # 左边去掉班级后剩余部分，尽量识别姓名
            if class_name:
                left_rest = left.replace(class_name, "", 1)
            else:
                left_rest = left
            # 剩余视为姓名
            name_guess = clean_token(left_rest)
            if name_guess and is_name_token(name_guess):
                student_name = name_guess
            # 右边视为作业名称
            title_guess = clean_token(right)
            if title_guess:
                assignment_title = title_guess

    # 若班级被误判为整串（包含学号/作业名），尝试精炼为“...班”
    if class_name and student_id and student_id in class_name:
        m_refine = re.search(r"(.+?班)", class_name)
        if m_refine:
            class_name = clean_token(m_refine.group(1))

    # 8) 特殊括号拼接格式：【班级】姓名【学号】作业名称
    if student_id and class_name and student_name is None:
        m_name = re.search(r"】\s*([^【\[\(（]{1,20})\s*[【\[\(（]", stem_norm)
        if m_name:
            name_guess = clean_token(m_name.group(1))
            if name_guess and is_name_token(name_guess):
                student_name = name_guess
    if student_id:
        m_title = re.search(r"[】\]\)）]\s*([^【]+)$", stem_norm)
        if m_title:
            title_guess = clean_token(m_title.group(1))
            if title_guess and (assignment_title is None or len(title_guess) < len(assignment_title)):
                assignment_title = title_guess

    # 9) 若完全识别不到学号与姓名，则认为无法解析
    if not student_id and not student_name:
        logger.warning("文件名无法识别出学号与姓名：%s；%s", filename, FILENAME_FORMAT_HINT)
        return FileMeta(
            original_name=filename,
            class_name=None,
            student_name=None,
            student_id=None,
            assignment_title=None,
        )

    # 10) 若仅识别到姓名但无法识别学号，默认不采信（避免误判）
    if student_id is None:
        logger.warning("文件名未识别到学号，已忽略姓名信息：%s；%s", filename, FILENAME_FORMAT_HINT)
        student_name = None
        class_name = None
        assignment_title = None

    return FileMeta(
        original_name=filename,
        class_name=class_name,
        student_name=student_name,
        student_id=student_id,
        assignment_title=assignment_title,
    )
