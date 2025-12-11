"""
文件工具模块，负责批次 ID 生成、文件保存与 docx 解析。
"""
from __future__ import annotations

import random
import string
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
    """简单从文件名推测学号与姓名，格式示例：2023001_张三.docx。"""
    stem = Path(filename).stem
    if "_" in stem:
        student_id, student_name = stem.split("_", 1)
        return student_id.strip(), student_name.strip()
    if "-" in stem:
        student_id, student_name = stem.split("-", 1)
        return student_id.strip(), student_name.strip()
    return None, None


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

