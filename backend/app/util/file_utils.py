"""
文件工具聚合模块，保持原有导出路径，同时将具体实现拆分至子模块。
"""
from __future__ import annotations

from app.util.files import (
    CONTENT_TOO_SHORT_MESSAGE,
    FILENAME_FORMAT_HINT,
    FORMAT_INVALID_MESSAGE,
    INVALID_EXTENSION_MESSAGE,
    PARSE_FAILED_MESSAGE,
    SUPPORTED_EXTENSIONS,
    FileMeta,
    extract_student_info,
    generate_batch_id,
    parse_docx_text,
    parse_file_text,
    parse_filename_meta,
    parse_text_file,
    save_upload_files,
    validate_docx_format,
    validate_supported_file,
)

__all__ = [
    "FileMeta",
    "extract_student_info",
    "parse_filename_meta",
    "generate_batch_id",
    "save_upload_files",
    "parse_docx_text",
    "parse_text_file",
    "parse_file_text",
    "validate_supported_file",
    "validate_docx_format",
    "SUPPORTED_EXTENSIONS",
    "INVALID_EXTENSION_MESSAGE",
    "CONTENT_TOO_SHORT_MESSAGE",
    "PARSE_FAILED_MESSAGE",
    "FILENAME_FORMAT_HINT",
    "FORMAT_INVALID_MESSAGE",
]
