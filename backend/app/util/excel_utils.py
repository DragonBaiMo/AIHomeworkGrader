"""
Excel 工具模块，负责成绩表与异常清单的生成。
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from openpyxl import Workbook

from app.util.logger import logger


class ExcelExporter:
    """成绩与异常导出工具。"""

    def __init__(self, batch_dir: Path) -> None:
        self.batch_dir = batch_dir

    def export_results(self, rows: Iterable[dict]) -> Path:
        """导出成绩结果 Excel。"""
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "成绩结果"
        headers = [
            "文件名",
            "学号",
            "姓名",
            "总分",
            "规则满分",
            "规则得分",
            "评分明细",
            "评语",
            "状态",
            "错误描述",
        ]
        sheet.append(headers)
        for row in rows:
            sheet.append(
                [
                    row.get("file_name"),
                    row.get("student_id"),
                    row.get("student_name"),
                    row.get("score"),
                    row.get("score_rubric_max"),
                    row.get("score_rubric"),
                    row.get("detail_json"),
                    row.get("comment"),
                    row.get("status"),
                    row.get("error_message"),
                ]
            )
        target = self.batch_dir / "grade_result.xlsx"
        workbook.save(target)
        logger.info("成绩表已生成：%s", target)
        return target

    def export_errors(self, rows: Iterable[dict]) -> Path:
        """导出异常清单 Excel。"""
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "异常清单"
        headers = ["文件名", "错误类型", "错误描述"]
        sheet.append(headers)
        for row in rows:
            sheet.append([row.get("file_name"), row.get("error_type"), row.get("error_message")])
        target = self.batch_dir / "error_list.xlsx"
        workbook.save(target)
        logger.info("异常清单已生成：%s", target)
        return target
