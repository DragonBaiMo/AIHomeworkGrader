"""
文件工具模块，负责批次 ID 生成、文件保存与 docx 解析。
"""
from __future__ import annotations

import random
import string
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Tuple

from docx import Document
from fastapi import UploadFile

from config.settings import UPLOAD_DIR
from app.util.logger import logger


INVALID_EXTENSION_MESSAGE = "文件格式错误：仅支持 .docx"
CONTENT_TOO_SHORT_MESSAGE = "正文过短，无法判定有效作业"
PARSE_FAILED_MESSAGE = "无法解析该 Word 文件，可能已损坏"
FILENAME_FORMAT_HINT = "文件命名应为“班级+姓名+学号+作业名称”，例如：25计算机科学与技术1班+张三三+202502210111+职业规划书"
FORMAT_INVALID_MESSAGE = "作业格式不符合要求：正文需宋体小四号，行间距1.5倍"


@dataclass
class FileMeta:
    """从文件名中解析出的基础元信息。"""

    original_name: str
    class_name: Optional[str]
    student_name: Optional[str]
    student_id: Optional[str]
    assignment_title: Optional[str]


def generate_batch_id(prefix: str = "batch") -> str:
    """生成批次 ID，格式为 prefix-年月日时分秒-随机串。"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}-{timestamp}-{rand}"


def save_upload_files(batch_id: str, files: Iterable[UploadFile]) -> Tuple[Path, list[Path]]:
    """将上传的文件保存到本地批次目录。"""
    batch_dir = UPLOAD_DIR / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)
    stored_paths: list[Path] = []
    for file in files:
        target = batch_dir / file.filename
        with target.open("wb") as f:
            content = file.file.read()
            f.write(content)
        logger.info("保存上传文件：%s", target)
        stored_paths.append(target)
    return batch_dir, stored_paths


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
    stem = Path(filename).stem
    parts = [p.strip() for p in stem.split("+") if p.strip()]
    if len(parts) < 4:
        logger.warning("文件名不符合规范：%s；%s", filename, FILENAME_FORMAT_HINT)
        return FileMeta(
            original_name=filename,
            class_name=None,
            student_name=None,
            student_id=None,
            assignment_title=None,
        )

    class_name, student_name, student_id, assignment_title = parts[0], parts[1], parts[2], parts[3]
    return FileMeta(
        original_name=filename,
        class_name=class_name or None,
        student_name=student_name or None,
        student_id=student_id or None,
        assignment_title=assignment_title or None,
    )


def parse_docx_text(file_path: Path, min_length: int = 50) -> str:
    """解析 docx 正文为纯文本，出错或字数不足时抛出异常。"""
    try:
        document = Document(file_path)
    except Exception as exc:  # noqa: BLE001
        logger.error("解析 docx 失败：%s", exc)
        raise ValueError(PARSE_FAILED_MESSAGE) from exc

    paragraphs = [para.text.strip() for para in document.paragraphs if para.text.strip()]
    content = "\n".join(paragraphs)
    if not content or len(content) < min_length:
        raise ValueError(CONTENT_TOO_SHORT_MESSAGE)
    return content


def validate_docx(file_path: Path) -> None:
    """校验文件是否为 docx。"""
    if file_path.suffix.lower() != ".docx":
        raise ValueError(INVALID_EXTENSION_MESSAGE)


def validate_docx_format(file_path: Path) -> None:
    """
    校验 docx 正文格式。

    要求：
    1. 文档中至少存在一段“正文”满足：字体为宋体（SimSun/宋体）、字号为小四（约 12pt）、行间距为 1.5 倍；
    2. 不要求全文所有段落都一致，但若全文找不到任何符合规范的正文段落，则判为格式异常。

    若不满足上述“至少一段合规正文”要求，则抛出异常，由上层归类为问题文件。
    """
    try:
        document = Document(file_path)
    except Exception as exc:  # noqa: BLE001
        logger.error("读取 docx 失败：%s", exc)
        raise ValueError(PARSE_FAILED_MESSAGE) from exc

    font_errors: list[str] = []
    size_errors: list[str] = []
    spacing_errors: list[str] = []
    has_valid_body = False

    def get_effective_font_name(run) -> Optional[str]:
        if run.font.name:
            return run.font.name
        if run.style and getattr(run.style, "font", None) and run.style.font.name:
            return run.style.font.name
        return None

    def get_effective_font_size(run) -> Optional[float]:
        if run.font.size:
            return float(run.font.size.pt)
        if run.style and getattr(run.style, "font", None) and run.style.font.size:
            return float(run.style.font.size.pt)
        return None

    def get_effective_line_spacing(para) -> Optional[float]:
        pf = para.paragraph_format
        if pf and pf.line_spacing:
            try:
                return float(pf.line_spacing)
            except Exception:  # noqa: BLE001
                return None
        style_pf = getattr(getattr(para, "style", None), "paragraph_format", None)
        if style_pf and style_pf.line_spacing:
            try:
                return float(style_pf.line_spacing)
            except Exception:  # noqa: BLE001
                return None
        return None

    for index, para in enumerate(document.paragraphs, start=1):
        if not para.text or not para.text.strip():
            continue

        spacing = get_effective_line_spacing(para)
        spacing_ok = spacing is not None and abs(spacing - 1.5) <= 0.1
        if not spacing_ok:
            spacing_errors.append(f"第{index}段行距={spacing if spacing is not None else '未设置'}")

        paragraph_has_valid_run = False
        for run in para.runs:
            if not run.text or not run.text.strip():
                continue
            font_name = get_effective_font_name(run)
            font_ok = font_name is not None and ("宋体" in font_name or "SimSun" in font_name)
            if not font_ok:
                font_errors.append(f"第{index}段字体={font_name if font_name else '未设置'}")

            font_size = get_effective_font_size(run)
            size_ok = font_size is not None and abs(font_size - 12.0) <= 0.5
            if not size_ok:
                size_errors.append(f"第{index}段字号={font_size if font_size is not None else '未设置'}pt")

            if font_ok and size_ok:
                paragraph_has_valid_run = True

        if spacing_ok and paragraph_has_valid_run:
            has_valid_body = True

    if not has_valid_body:
        details: list[str] = []
        if font_errors:
            details.append("字体问题：" + "；".join(font_errors[:5]))
        if size_errors:
            details.append("字号问题：" + "；".join(size_errors[:5]))
        if spacing_errors:
            details.append("行距问题：" + "；".join(spacing_errors[:5]))
        message = FORMAT_INVALID_MESSAGE + "。"
        if details:
            message += " " + "；".join(details)
        raise ValueError(message)
