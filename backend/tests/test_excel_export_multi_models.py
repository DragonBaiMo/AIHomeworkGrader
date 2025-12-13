"""Excel 导出（多模型列）回归测试。"""
from __future__ import annotations

import sys
from pathlib import Path

from openpyxl import load_workbook

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.util.excel_utils import ExcelExporter


def test_export_results_contains_multi_model_headers(tmp_path: Path) -> None:
    exporter = ExcelExporter(tmp_path)
    exporter.export_results(
        [
            {
                "file_name": "张三.docx",
                "student_id": "2025001",
                "student_name": "张三",
                "score": 55.0,
                "score_rubric": 45.0,
                "score_rubric_max": 60.0,
                "status": "成功",
                "error_message": None,
                "comment": "总体评语",
                "detail_json": None,
                "aggregate_strategy": "mean",
                "grader_results": [
                    {"model_index": 1, "api_url": "http://a", "model_name": "m1", "score": 55, "comment": "c1", "error_message": None, "latency_ms": 100},
                    {"model_index": 2, "api_url": "http://a", "model_name": "m2", "score": 57, "comment": "c2", "error_message": None, "latency_ms": 120},
                    {"model_index": 3, "api_url": "http://b", "model_name": "m3", "score": None, "comment": None, "error_message": "失败", "latency_ms": 300},
                ],
            }
        ],
        summary={"批次ID": "batch-demo"},
        error_rows=[],
    )

    path = tmp_path / "grade_result.xlsx"
    workbook = load_workbook(path)
    sheet = workbook["成绩总表"]
    headers = [cell.value for cell in sheet[1]]
    assert "聚合算法" in headers
    assert "默认模型分数" in headers
    assert "追加模型1分数" in headers
    assert "追加模型2分数" in headers

    sheet_default = workbook["默认模型结果"]
    headers_default = [cell.value for cell in sheet_default[1]]
    assert "接口" in headers_default
    assert "模型名称" in headers_default
    assert "耗时ms" in headers_default
