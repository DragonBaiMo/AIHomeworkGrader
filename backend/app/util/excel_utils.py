"""
Excel 工具模块，负责成绩表与异常清单的生成。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from app.util.logger import logger


class ExcelExporter:
    """成绩与异常导出工具。"""

    def __init__(self, batch_dir: Path) -> None:
        self.batch_dir = batch_dir

    @staticmethod
    def _parse_detail_json(detail_json: Optional[str]) -> Optional[dict[str, Any]]:
        if not detail_json:
            return None
        try:
            data = json.loads(detail_json)
            if isinstance(data, dict):
                return data
        except Exception:  # noqa: BLE001
            return None
        return None

    def export_results(self, rows: Iterable[dict], summary: Optional[dict[str, Any]] = None, error_rows: Optional[Iterable[dict]] = None) -> Path:
        """导出成绩结果 Excel（多工作表）。"""
        workbook = Workbook()
        sheet_summary = workbook.active
        sheet_summary.title = "批次总览"
        sheet_summary.append(["字段", "值"])
        if summary:
            for key, value in summary.items():
                sheet_summary.append([str(key), "" if value is None else str(value)])
        # 美化 Summary 表
        summary_font = Font(bold=True)
        summary_fill = PatternFill("solid", fgColor="F2F2F2")
        for col in range(1, 3):
            cell = sheet_summary.cell(row=1, column=col)
            cell.font = summary_font
            cell.fill = summary_fill
        for row in sheet_summary.iter_rows(min_row=1, min_col=2, max_col=2):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="center")
        sheet_summary.column_dimensions["A"].width = 24
        sheet_summary.column_dimensions["B"].width = 48
        sheet_summary.freeze_panes = "A2"

        sheet_scores = workbook.create_sheet("成绩总表")
        sheet_scores.append(
            [
                "文件名",
                "学号",
                "姓名",
                "最终分（目标满分）",
                "聚合算法",
                "默认模型分数",
                "追加模型1分数",
                "追加模型2分数",
                "状态",
                "错误描述",
                "总体评语（多模型：主模型二次生成）",
            ]
        )

        sheet_model_default = workbook.create_sheet("默认模型结果")
        sheet_model_default.append(["文件名", "学号", "姓名", "接口", "模型名称", "分数", "规则得分", "规则满分", "状态", "错误描述", "评语", "耗时ms"])

        sheet_model_1 = workbook.create_sheet("追加模型1结果")
        sheet_model_1.append(["文件名", "学号", "姓名", "接口", "模型名称", "分数", "规则得分", "规则满分", "状态", "错误描述", "评语", "耗时ms"])

        sheet_model_2 = workbook.create_sheet("追加模型2结果")
        sheet_model_2.append(["文件名", "学号", "姓名", "接口", "模型名称", "分数", "规则得分", "规则满分", "状态", "错误描述", "评语", "耗时ms"])

        sheet_dimensions = workbook.create_sheet("维度汇总")
        sheet_dimensions.append(
            [
                "文件名",
                "学号",
                "姓名",
                "维度名称",
                "维度得分",
                "维度满分",
                "维度评语",
            ]
        )

        sheet_criteria = workbook.create_sheet("细则明细")
        sheet_criteria.append(
            [
                "文件名",
                "学号",
                "姓名",
                "维度名称",
                "细则名称",
                "细则得分",
                "细则满分",
                "扣分原因/得分依据",
            ]
        )

        if error_rows:
            sheet_errors = workbook.create_sheet("异常清单")
            sheet_errors.append(["文件名", "错误类型", "错误描述"])
            for col in range(1, 4):
                cell = sheet_errors.cell(row=1, column=col)
                cell.font = Font(bold=True)
                cell.fill = PatternFill("solid", fgColor="FDF2F2")
            sheet_errors.column_dimensions["A"].width = 32
            sheet_errors.column_dimensions["B"].width = 16
            sheet_errors.column_dimensions["C"].width = 48
            for row in error_rows:
                sheet_errors.append([row.get("file_name"), row.get("error_type"), row.get("error_message")])

        header_style = Font(bold=True)
        header_fill = PatternFill("solid", fgColor="DCE6F1")
        border_side = Side(border_style="thin", color="DDDDDD")
        sheet_scores.row_dimensions[1].height = 22
        for col in range(1, sheet_scores.max_column + 1):
            cell = sheet_scores.cell(row=1, column=col)
            cell.font = header_style
            cell.fill = header_fill
            cell.border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)
            cell.alignment = Alignment(horizontal="center", vertical="center")
        sheet_dimensions.row_dimensions[1].height = 22
        for col in range(1, sheet_dimensions.max_column + 1):
            cell = sheet_dimensions.cell(row=1, column=col)
            cell.font = header_style
            cell.fill = header_fill
            cell.border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)
            cell.alignment = Alignment(horizontal="center", vertical="center")
        sheet_criteria.row_dimensions[1].height = 22
        for col in range(1, sheet_criteria.max_column + 1):
            cell = sheet_criteria.cell(row=1, column=col)
            cell.font = header_style
            cell.fill = header_fill
            cell.border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for sheet in (sheet_model_default, sheet_model_1, sheet_model_2):
            sheet.row_dimensions[1].height = 22
            for col in range(1, sheet.max_column + 1):
                cell = sheet.cell(row=1, column=col)
                cell.font = header_style
                cell.fill = header_fill
                cell.border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)
                cell.alignment = Alignment(horizontal="center", vertical="center")

        sheet_scores.column_dimensions["A"].width = 28
        sheet_scores.column_dimensions["B"].width = 12
        sheet_scores.column_dimensions["C"].width = 12
        sheet_scores.column_dimensions["D"].width = 16
        sheet_scores.column_dimensions["E"].width = 12
        sheet_scores.column_dimensions["F"].width = 14
        sheet_scores.column_dimensions["G"].width = 14
        sheet_scores.column_dimensions["H"].width = 14
        sheet_scores.column_dimensions["I"].width = 10
        sheet_scores.column_dimensions["J"].width = 28
        sheet_scores.column_dimensions["K"].width = 36

        for sheet in (sheet_model_default, sheet_model_1, sheet_model_2):
            sheet.column_dimensions["A"].width = 28
            sheet.column_dimensions["B"].width = 12
            sheet.column_dimensions["C"].width = 12
            sheet.column_dimensions["D"].width = 28
            sheet.column_dimensions["E"].width = 22
            sheet.column_dimensions["F"].width = 12
            sheet.column_dimensions["G"].width = 12
            sheet.column_dimensions["H"].width = 12
            sheet.column_dimensions["I"].width = 10
            sheet.column_dimensions["J"].width = 28
            sheet.column_dimensions["K"].width = 36
            sheet.column_dimensions["L"].width = 12
        sheet_dimensions.column_dimensions["A"].width = 28
        sheet_dimensions.column_dimensions["B"].width = 12
        sheet_dimensions.column_dimensions["C"].width = 12
        sheet_dimensions.column_dimensions["D"].width = 22
        sheet_dimensions.column_dimensions["E"].width = 12
        sheet_dimensions.column_dimensions["F"].width = 12
        sheet_dimensions.column_dimensions["G"].width = 32
        sheet_criteria.column_dimensions["A"].width = 28
        sheet_criteria.column_dimensions["B"].width = 12
        sheet_criteria.column_dimensions["C"].width = 12
        sheet_criteria.column_dimensions["D"].width = 22
        sheet_criteria.column_dimensions["E"].width = 24
        sheet_criteria.column_dimensions["F"].width = 12
        sheet_criteria.column_dimensions["G"].width = 12
        sheet_criteria.column_dimensions["H"].width = 36
        for col in range(1, sheet_scores.max_column + 1):
            sheet_scores.cell(row=1, column=col).alignment = Alignment(horizontal="center", vertical="center")
        sheet_scores.freeze_panes = "A2"
        sheet_dimensions.freeze_panes = "A2"
        sheet_criteria.freeze_panes = "A2"
        sheet_model_default.freeze_panes = "A2"
        sheet_model_1.freeze_panes = "A2"
        sheet_model_2.freeze_panes = "A2"

        for row in rows:
            file_name = row.get("file_name")
            student_id = row.get("student_id")
            student_name = row.get("student_name")
            status = row.get("status")
            score = row.get("score")
            score_rubric = row.get("score_rubric")
            score_rubric_max = row.get("score_rubric_max")
            error_message = row.get("error_message")
            comment = row.get("comment")
            aggregate_strategy = row.get("aggregate_strategy") or ""
            grader_results = row.get("grader_results") or []
            by_index: dict[int, dict[str, Any]] = {}
            if isinstance(grader_results, list):
                for item in grader_results:
                    if isinstance(item, dict):
                        try:
                            idx = int(item.get("model_index"))
                        except Exception:  # noqa: BLE001
                            continue
                        by_index[idx] = item

            sheet_scores.append(
                [
                    file_name,
                    student_id,
                    student_name,
                    score,
                    aggregate_strategy,
                    (by_index.get(1) or {}).get("score"),
                    (by_index.get(2) or {}).get("score"),
                    (by_index.get(3) or {}).get("score"),
                    status,
                    error_message,
                    comment,
                ]
            )

            def append_model_row(sheet, idx: int) -> None:
                info = by_index.get(idx) or {}
                sheet.append(
                    [
                        file_name,
                        student_id,
                        student_name,
                        info.get("api_url"),
                        info.get("model_name"),
                        info.get("score"),
                        info.get("score_rubric"),
                        info.get("score_rubric_max"),
                        info.get("status"),
                        info.get("error_message"),
                        info.get("comment"),
                        info.get("latency_ms"),
                    ]
                )

            append_model_row(sheet_model_default, 1)
            append_model_row(sheet_model_1, 2)
            append_model_row(sheet_model_2, 3)

            if status != "成功":
                continue
            detail = self._parse_detail_json(row.get("detail_json"))
            if not detail:
                continue
            sections = detail.get("sections")
            if not isinstance(sections, list):
                continue
            for sec in sections:
                if not isinstance(sec, dict):
                    continue
                sec_name = sec.get("name")
                sec_score = sec.get("score")
                sec_max = sec.get("max_score")
                sec_comment = sec.get("comment")
                sheet_dimensions.append([file_name, student_id, student_name, sec_name, sec_score, sec_max, sec_comment])

                items = sec.get("items")
                if not isinstance(items, list):
                    continue
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    sheet_criteria.append(
                        [
                            file_name,
                            student_id,
                            student_name,
                            sec_name,
                            item.get("name"),
                            item.get("score"),
                            item.get("max_score"),
                            item.get("comment"),
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
