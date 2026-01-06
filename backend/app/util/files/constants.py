"""文件处理常量定义，统一存放提示文本与受支持格式。"""
from __future__ import annotations

SUPPORTED_EXTENSIONS = {".docx", ".md", ".markdown", ".txt"}
INVALID_EXTENSION_MESSAGE = "文件格式错误：仅支持 .docx/.md/.markdown/.txt"
CONTENT_TOO_SHORT_MESSAGE = "正文过短，无法判定有效作业"
PARSE_FAILED_MESSAGE = "无法解析该 Word 文件，可能已损坏"
FILENAME_FORMAT_HINT = "文件命名建议包含班级、姓名、学号、作业名称，例如：25计算机科学与技术1班+张三三+202502210111+职业规划书"
FORMAT_INVALID_MESSAGE = "作业格式不符合要求：正文需宋体小四号，行间距1.5倍"

# 解析规则（集中配置，便于统一调整）
STUDENT_ID_REGEX = r"(?<!\d)\d{6,20}(?!\d)"
NAME_REGEXES = [
    r"[\u4e00-\u9fff·•]{2,10}",
    r"[A-Za-z][A-Za-z.\-\s]{1,30}",
]
CLASS_KEYWORDS_REGEX = r"(?:班|class)"
SEPARATOR_REGEX = r"[+_\-@|.\s]+"
TITLE_KEYWORDS = [
    "专业认知实践报告",
    "专业认知报告",
    "专业认知分析",
    "专业分析报告",
    "职业分析报告",
    "职业规划书",
    "专业分析作业",
    "专业分析导论",
    "职业规划",
    "专业分析",
    "专业认知",
    "作业",
    "报告",
    "模板",
]
# 目录列表前缀（时间/大小或 PowerShell 列表）
DIR_LISTING_PREFIX_REGEXES = [
    r"^\s*\d{1,2}:\d{2}\s+\d+\s+",
    r"^\s*-a----\s+\d{4}/\d{2}/\d{2}\s+\d{1,2}:\d{2}\s+\d+\s+",
]
