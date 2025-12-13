"""文件处理常量定义，统一存放提示文本与受支持格式。"""
from __future__ import annotations

SUPPORTED_EXTENSIONS = {".docx", ".md", ".markdown", ".txt"}
INVALID_EXTENSION_MESSAGE = "文件格式错误：仅支持 .docx/.md/.markdown/.txt"
CONTENT_TOO_SHORT_MESSAGE = "正文过短，无法判定有效作业"
PARSE_FAILED_MESSAGE = "无法解析该 Word 文件，可能已损坏"
FILENAME_FORMAT_HINT = "文件命名建议包含班级、姓名、学号、作业名称，例如：25计算机科学与技术1班+张三三+202502210111+职业规划书"
FORMAT_INVALID_MESSAGE = "作业格式不符合要求：正文需宋体小四号，行间距1.5倍"
