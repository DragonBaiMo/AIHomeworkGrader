"""文件处理子包，按职责拆分文件解析、校验与存储。"""
from app.util.files.constants import (
    CONTENT_TOO_SHORT_MESSAGE,
    FILENAME_FORMAT_HINT,
    FORMAT_INVALID_MESSAGE,
    INVALID_EXTENSION_MESSAGE,
    PARSE_FAILED_MESSAGE,
    SUPPORTED_EXTENSIONS,
)
from app.util.files.meta import FileMeta, extract_student_info, parse_filename_meta
from app.util.files.parsing import parse_docx_text, parse_file_text, parse_text_file, validate_supported_file
from app.util.files.storage import generate_batch_id, save_upload_files
from app.util.files.validation import validate_docx_format

__all__ = [
    "CONTENT_TOO_SHORT_MESSAGE",
    "FILENAME_FORMAT_HINT",
    "FORMAT_INVALID_MESSAGE",
    "INVALID_EXTENSION_MESSAGE",
    "PARSE_FAILED_MESSAGE",
    "SUPPORTED_EXTENSIONS",
    "FileMeta",
    "extract_student_info",
    "parse_filename_meta",
    "parse_docx_text",
    "parse_file_text",
    "parse_text_file",
    "validate_supported_file",
    "generate_batch_id",
    "save_upload_files",
    "validate_docx_format",
]
