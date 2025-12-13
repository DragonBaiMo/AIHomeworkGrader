"""docx 兜底解析逻辑单元测试。"""
from __future__ import annotations

import sys
from pathlib import Path
import zipfile

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.util.file_utils import parse_file_text


def test_parse_docx_text_fallback_via_document_xml(tmp_path: Path) -> None:
    docx_path = tmp_path / "仅包含正文.xml.docx"
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>第一段</w:t></w:r></w:p>
    <w:p><w:r><w:t>第二段</w:t></w:r></w:p>
  </w:body>
</w:document>
"""
    with zipfile.ZipFile(docx_path, "w") as zf:
        zf.writestr("word/document.xml", document_xml)

    content = parse_file_text(docx_path, min_length=1)
    assert "第一段" in content
    assert "第二段" in content

