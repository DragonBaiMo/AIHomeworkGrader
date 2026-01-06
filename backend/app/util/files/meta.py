"""文件元信息解析，负责文件名拆解与识别。"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from app.util.files.constants import (
    CLASS_KEYWORDS_REGEX,
    DIR_LISTING_PREFIX_REGEXES,
    FILENAME_FORMAT_HINT,
    NAME_REGEXES,
    SEPARATOR_REGEX,
    STUDENT_ID_REGEX,
    TITLE_KEYWORDS,
)
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
        for pat in DIR_LISTING_PREFIX_REGEXES:
            text = re.sub(pat, "", text)
        text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
        fullwidth = "，。；：？！【】（）％＃＠＆＋－＝＿“”‘’、．《》"
        halfwidth = ",.;:?![]()%#@&+-=_\"\"'',.<>"
        text = text.translate(str.maketrans(fullwidth, halfwidth))
        text = re.sub(r"(班|级)的", r"\1 ", text)
        return (
            text.replace("｜", "|")
            .replace("‖", "|")
            .replace("·", "·")
            .replace("—", "-")
            .replace("–", "-")
            .strip()
        )

    stem_norm = normalize_text(stem)

    def clean_token(token: str) -> str:
        t = token.strip()
        # 去掉常见外壳
        t = re.sub(r"^[【\[\(（《<]+|[】\]\)）》>]+$", "", t).strip()
        # 去掉前缀噪音
        t = re.sub(r"^(作业提交|作业|Homework|HOMEWORK|作业_提交)[:：_\-]*", "", t).strip()
        return t

    def normalize_title(t: str) -> str:
        t = clean_token(t)
        t = re.sub(r"[\(（\[]\d+\)$", "", t)
        t = re.sub(r"[\(（\[]\d+$", "", t)
        t = re.sub(r"[）\]\)]+$", "", t)
        t = clean_token(t)
        for keyword in TITLE_KEYWORDS:
            if keyword in t:
                return keyword
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

    def guess_student_id(text: str) -> Optional[str]:
        candidates = re.findall(STUDENT_ID_REGEX, text)
        if not candidates:
            return None
        return sorted(candidates, key=len, reverse=True)[0]

    def is_class_token(t: str) -> bool:
        return re.search(CLASS_KEYWORDS_REGEX, t, flags=re.IGNORECASE) is not None

    def is_name_token(t: str) -> bool:
        for pat in NAME_REGEXES:
            if re.fullmatch(pat, t):
                return True
        return False

    def is_title_like(t: str) -> bool:
        return any(keyword in t for keyword in TITLE_KEYWORDS)

    def strip_copy_suffix(t: str) -> str:
        t = re.sub(r"[\(（\[]\d+\)[）\]\)]?", "", t)
        return clean_token(t)

    def extract_class_name(text: str) -> Optional[str]:
        matches = re.findall(r"[\u4e00-\u9fff0-9·\s]{0,30}班", text)
        if not matches:
            return None
        raw = max(matches, key=len)
        return clean_token(re.sub(r"\s+", "", raw))

    def remove_class(text: str, class_text: Optional[str]) -> str:
        if class_text and class_text in text:
            text = text.replace(class_text, "", 1)
            return clean_token(text)
        if "班" in text:
            matches = re.findall(r"[\u4e00-\u9fff0-9·\s]{0,30}班", text)
            if matches:
                raw = max(matches, key=len)
                text = text.replace(raw, "", 1)
        return clean_token(text)

    def extract_title(text: str) -> Optional[str]:
        cleaned = strip_copy_suffix(clean_token(text))
        for keyword in TITLE_KEYWORDS:
            if keyword in cleaned:
                return keyword
        return None

    def extract_name(text: str, title: Optional[str]) -> Optional[str]:
        cleaned = clean_token(text)
        if not cleaned:
            return None
        cleaned = re.sub(r"[（(][^）)]*[）)]", "", cleaned)
        if title:
            cleaned = clean_token(cleaned.replace(title, ""))
        candidates = re.findall(r"[\u4e00-\u9fff·•]{2,10}", cleaned)
        candidates = [c for c in candidates if not is_class_token(c) and not is_title_like(c)]
        if not candidates:
            return None
        noise_keywords = ["华为", "创新班", "鲲鹏", "云创新班", "ICT"]
        filtered = [c for c in candidates if not any(k in c for k in noise_keywords)]
        for cand in filtered:
            if "科" in cand and "班" not in cand:
                continue
            return cand
        return filtered[0] if filtered else None

    # 2) 统一分隔符切分（支持 + _ - | . @ 空格）
    tokens = [clean_token(t) for t in re.split(SEPARATOR_REGEX, stem_norm) if clean_token(t)]

    student_id = guess_student_id(stem_norm)
    class_name: Optional[str] = None
    student_name: Optional[str] = None
    assignment_title: Optional[str] = None

    if student_id:
        left, right = stem_norm.split(student_id, 1)
        left = clean_token(left)
        right = clean_token(right)

        class_name = extract_class_name(left) or extract_class_name(right) or extract_class_name(stem_norm)
        class_name = clean_token(class_name) if class_name else None
        if class_name and "班" in left and class_name not in left and right:
            class_name = extract_class_name(right) or class_name
        if class_name and is_class_token(class_name):
            m_refine = re.search(r"(.+?班)", class_name)
            if m_refine:
                class_name = clean_token(m_refine.group(1))
            m_digit = re.search(r"\d", class_name)
            if m_digit:
                class_name = clean_token(class_name[m_digit.start() :])

        title_from_right = extract_title(right)
        title_from_left = extract_title(left)
        assignment_title = title_from_right or title_from_left
        title_on_right = title_from_right is not None

        left_wo_class = remove_class(left, class_name)
        right_wo_class = remove_class(right, class_name)

        right_for_name = right_wo_class
        left_for_name = left_wo_class
        if not right_for_name and "班" in left:
            left_for_name = remove_class(left, None)
        if not right_for_name and "班" in right:
            right_for_name = remove_class(right, None)
        right_name = extract_name(right_for_name, assignment_title)
        left_name = extract_name(left_for_name, assignment_title)
        if left_name and right_name:
            if title_on_right:
                student_name = left_name
            elif len(right_name) <= 2 and len(left_name) >= 2:
                student_name = left_name
            else:
                student_name = right_name
        else:
            student_name = right_name or left_name

    if assignment_title is None:
        for t in reversed(tokens):
            if is_title_like(t):
                assignment_title = normalize_title(t)
                break


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
