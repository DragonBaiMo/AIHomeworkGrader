"""文件内容解析模块，负责读取与转换正文。"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from docx import Document

from app.util.files.constants import CONTENT_TOO_SHORT_MESSAGE, INVALID_EXTENSION_MESSAGE, PARSE_FAILED_MESSAGE, SUPPORTED_EXTENSIONS
from app.util.logger import logger


def validate_supported_file(file_path: Path) -> None:
    """校验文件扩展名是否在允许范围内。"""
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(INVALID_EXTENSION_MESSAGE)


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


def parse_text_file(file_path: Path, min_length: int = 50) -> str:
    """读取纯文本/Markdown 文件内容，出错或字数不足时抛出异常。"""
    try:
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="gb18030")
    except Exception as exc:  # noqa: BLE001
        logger.error("读取文本文件失败：%s", exc)
        raise ValueError("无法读取该文本文件，可能编码不受支持或文件已损坏") from exc

    content = content.strip()
    if not content or len(content) < min_length:
        raise ValueError(CONTENT_TOO_SHORT_MESSAGE)
    return content


def parse_file_text(file_path: Path, min_length: int = 50) -> str:
    """根据扩展名解析文件为正文纯文本。"""
    suffix = file_path.suffix.lower()
    if suffix == ".docx":
        return parse_docx_text(file_path, min_length=min_length)
    return parse_text_file(file_path, min_length=min_length)
