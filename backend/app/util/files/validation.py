"""文档格式校验逻辑，聚焦 docx 样式检查。"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from docx import Document

from app.util.files.constants import FORMAT_INVALID_MESSAGE, PARSE_FAILED_MESSAGE
from app.util.logger import logger


def validate_docx_format(
    file_path: Path,
    *,
    allowed_font_keywords: Optional[list[str]] = None,
    allowed_font_size_pts: Optional[list[float]] = None,
    font_size_tolerance: float = 0.5,
    target_line_spacing: Optional[float] = 1.5,
    line_spacing_tolerance: Optional[float] = 0.1,
) -> None:
    """
    校验 docx 正文格式。

    要求：
    1. 文档中至少存在一段“正文”满足：字体为宋体（SimSun/宋体）、字号为小四（约 12pt）、行间距为 1.5 倍；
    2. 不要求全文所有段落都一致，但若全文找不到任何符合规范的正文段落，则判为格式异常。

    若不满足上述“至少一段合规正文”要求，则抛出异常，由上层归类为问题文件。
    """
    # 说明：此校验仅用于内部流程控制，不参与任何提示词构造与大模型输入。
    try:
        document = Document(file_path)
    except Exception as exc:  # noqa: BLE001
        logger.error("读取 docx 失败：%s", exc)
        raise ValueError(PARSE_FAILED_MESSAGE) from exc

    # 默认规则：宋体小四（12pt）、行距 1.5 倍；误差用于兼容不同 Word 环境。
    if not allowed_font_keywords:
        allowed_font_keywords = ["宋体", "SimSun"]
    if not allowed_font_size_pts:
        allowed_font_size_pts = [12.0]

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
        spacing_ok = True
        if target_line_spacing is not None and line_spacing_tolerance is not None:
            spacing_ok = spacing is not None and abs(spacing - float(target_line_spacing)) <= float(line_spacing_tolerance)
        if not spacing_ok:
            spacing_errors.append(f"第{index}段行距={spacing if spacing is not None else '未设置'}")

        paragraph_has_valid_run = False
        for run in para.runs:
            if not run.text or not run.text.strip():
                continue
            font_name = get_effective_font_name(run)
            font_ok = font_name is not None and any(k in font_name for k in allowed_font_keywords)
            if not font_ok:
                font_errors.append(f"第{index}段字体={font_name if font_name else '未设置'}")

            font_size = get_effective_font_size(run)
            size_ok = False
            if font_size is not None:
                size_ok = any(abs(font_size - float(t)) <= font_size_tolerance for t in allowed_font_size_pts)
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
