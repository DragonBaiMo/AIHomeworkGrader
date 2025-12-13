"""
Excel 工具模块，负责成绩表与异常清单的生成。
"""
from __future__ import annotations

import json
import statistics
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
    def _detect_model_count(rows: list[dict]) -> int:
        max_idx = 1
        for row in rows:
            results = row.get("grader_results") or []
            if not isinstance(results, list):
                continue
            for item in results:
                if not isinstance(item, dict):
                    continue
                try:
                    idx = int(item.get("model_index") or 0)
                except Exception:  # noqa: BLE001
                    continue
                if idx > max_idx:
                    max_idx = idx
        return max(1, min(3, max_idx))

    @staticmethod
    def _model_label(model_index: int) -> str:
        if model_index == 1:
            return "主模型"
        if model_index == 2:
            return "副模型1"
        if model_index == 3:
            return "副模型2"
        return f"模型{model_index}"

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
        rows_list = list(rows)
        model_count = self._detect_model_count(rows_list)

        workbook = Workbook()
        sheet_overview = workbook.active
        sheet_overview.title = "成绩总览"
        sheet_overview.append(["文件名", "学号", "姓名", "最终分（目标满分）", "聚合算法", "成功模型数", "失败模型数", "总体评语", "状态", "错误描述"])

        sheet_models = workbook.create_sheet("批改模型结果")
        model_headers: list[str] = []
        for idx in range(1, model_count + 1):
            label = self._model_label(idx)
            model_headers.extend([f"{label}名称", f"{label}分数", f"{label}评语"])
        sheet_models.append(["文件名", "学号", "姓名", *model_headers, "LLM总评语（多模型：主模型二次生成）"])

        sheet_dimensions = workbook.create_sheet("维度汇总")
        dim_headers: list[str] = []
        for idx in range(1, model_count + 1):
            dim_headers.append(f"{self._model_label(idx)}得分")
        sheet_dimensions.append(
            [
                "文件名",
                "学号",
                "姓名",
                "维度名称",
                "汇总得分（成功模型均值）",
                "维度满分",
                *dim_headers,
                "参与模型数",
                "分歧度（极差）",
                "维度评语（取主模型）",
            ]
        )

        sheet_criteria = workbook.create_sheet("细则明细")
        criteria_headers: list[str] = []
        for idx in range(1, model_count + 1):
            criteria_headers.append(f"{self._model_label(idx)}得分")
        sheet_criteria.append(
            [
                "文件名",
                "学号",
                "姓名",
                "维度名称",
                "细则名称",
                "汇总得分（成功模型均值）",
                "细则满分",
                *criteria_headers,
                "参与模型数",
                "分歧度（极差）",
                "扣分原因/得分依据（取主模型）",
            ]
        )

        sheet_summary = workbook.create_sheet("批次总览")
        sheet_summary.append(["字段", "值"])
        if summary:
            for key, value in summary.items():
                sheet_summary.append([str(key), "" if value is None else str(value)])

        sheet_errors = workbook.create_sheet("错误")
        sheet_errors.append(["文件名", "错误类型", "错误描述"])
        if error_rows:
            for row in error_rows:
                sheet_errors.append([row.get("file_name"), row.get("error_type"), row.get("error_message")])

        header_style = Font(bold=True)
        header_fill = PatternFill("solid", fgColor="DCE6F1")
        border_side = Side(border_style="thin", color="DDDDDD")
        def style_sheet(sheet) -> None:
            sheet.row_dimensions[1].height = 22
            for col in range(1, sheet.max_column + 1):
                cell = sheet.cell(row=1, column=col)
                cell.font = header_style
                cell.fill = header_fill
                cell.border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            sheet.freeze_panes = "A2"

        for sheet in (sheet_overview, sheet_models, sheet_dimensions, sheet_criteria, sheet_summary, sheet_errors):
            style_sheet(sheet)

        summary_font = Font(bold=True)
        summary_fill = PatternFill("solid", fgColor="F2F2F2")
        for col in range(1, 3):
            cell = sheet_summary.cell(row=1, column=col)
            cell.font = summary_font
            cell.fill = summary_fill
        sheet_summary.column_dimensions["A"].width = 24
        sheet_summary.column_dimensions["B"].width = 56
        for row in sheet_summary.iter_rows(min_row=1, min_col=2, max_col=2):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="center")

        sheet_overview.column_dimensions["A"].width = 32
        sheet_overview.column_dimensions["B"].width = 14
        sheet_overview.column_dimensions["C"].width = 14
        sheet_overview.column_dimensions["D"].width = 22
        sheet_overview.column_dimensions["E"].width = 14
        sheet_overview.column_dimensions["F"].width = 12
        sheet_overview.column_dimensions["G"].width = 12
        sheet_overview.column_dimensions["H"].width = 46
        sheet_overview.column_dimensions["I"].width = 10
        sheet_overview.column_dimensions["J"].width = 36

        sheet_models.column_dimensions["A"].width = 32
        sheet_models.column_dimensions["B"].width = 14
        sheet_models.column_dimensions["C"].width = 14
        for col in range(4, sheet_models.max_column + 1):
            sheet_models.column_dimensions[get_column_letter(col)].width = 24
        sheet_models.column_dimensions[get_column_letter(sheet_models.max_column)].width = 46

        sheet_errors.column_dimensions["A"].width = 32
        sheet_errors.column_dimensions["B"].width = 16
        sheet_errors.column_dimensions["C"].width = 56

        sheet_dimensions.column_dimensions["A"].width = 32
        sheet_dimensions.column_dimensions["B"].width = 14
        sheet_dimensions.column_dimensions["C"].width = 14
        sheet_dimensions.column_dimensions["D"].width = 22
        sheet_dimensions.column_dimensions["E"].width = 26
        sheet_dimensions.column_dimensions["F"].width = 12
        for col in range(7, sheet_dimensions.max_column + 1):
            sheet_dimensions.column_dimensions[get_column_letter(col)].width = 14
        sheet_dimensions.column_dimensions[get_column_letter(sheet_dimensions.max_column)].width = 32

        sheet_criteria.column_dimensions["A"].width = 32
        sheet_criteria.column_dimensions["B"].width = 14
        sheet_criteria.column_dimensions["C"].width = 14
        sheet_criteria.column_dimensions["D"].width = 22
        sheet_criteria.column_dimensions["E"].width = 26
        sheet_criteria.column_dimensions["F"].width = 26
        sheet_criteria.column_dimensions["G"].width = 12
        for col in range(8, sheet_criteria.max_column + 1):
            sheet_criteria.column_dimensions[get_column_letter(col)].width = 14
        sheet_criteria.column_dimensions[get_column_letter(sheet_criteria.max_column)].width = 46

        def normalize_model_comment(info: dict[str, Any]) -> str:
            if info.get("status") != "成功":
                err = str(info.get("error_message") or "").strip()
                return f"失败：{err}" if err else "失败"
            return str(info.get("comment") or "").strip()

        for row in rows_list:
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

            model_success_count = 0
            model_fail_count = 0
            for idx in (1, 2, 3):
                info = by_index.get(idx) or {}
                if info.get("status") == "成功":
                    model_success_count += 1
                elif info:
                    model_fail_count += 1

            sheet_overview.append(
                [
                    file_name,
                    student_id,
                    student_name,
                    score,
                    aggregate_strategy,
                    model_success_count,
                    model_fail_count,
                    comment,
                    status,
                    error_message,
                ]
            )

            sheet_models.append(
                [file_name, student_id, student_name]
                + sum(
                    (
                        [
                            str((by_index.get(idx) or {}).get("model_name") or ""),
                            (by_index.get(idx) or {}).get("score"),
                            normalize_model_comment(by_index.get(idx) or {}),
                        ]
                        for idx in range(1, model_count + 1)
                    ),
                    [],
                )
                + [comment]
            )

            def extract_sections(model_idx: int) -> list[dict[str, Any]]:
                info = by_index.get(model_idx) or {}
                sections = info.get("sections")
                if not isinstance(sections, list):
                    return []
                out: list[dict[str, Any]] = []
                for sec in sections:
                    if isinstance(sec, dict) and sec.get("name"):
                        out.append(sec)
                return out

            sections_by_model = {idx: extract_sections(idx) for idx in range(1, model_count + 1)}
            # 维度汇总（按维度名对齐，汇总为成功模型均值）
            dimension_names: set[str] = set()
            for idx in range(1, model_count + 1):
                for sec in sections_by_model.get(idx, []):
                    dimension_names.add(str(sec.get("name")))

            wrote_dim_rows = False
            for dim_name in sorted(dimension_names):
                scores_by_model: dict[int, Optional[float]] = {idx: None for idx in range(1, model_count + 1)}
                max_score: Optional[float] = None
                main_comment: Optional[str] = None
                for idx in range(1, model_count + 1):
                    sec = next((s for s in sections_by_model.get(idx, []) if str(s.get("name")) == dim_name), None)
                    if not isinstance(sec, dict):
                        continue
                    try:
                        scores_by_model[idx] = float(sec.get("score")) if sec.get("score") is not None else None
                    except Exception:  # noqa: BLE001
                        scores_by_model[idx] = None
                    if max_score is None and sec.get("max_score") is not None:
                        try:
                            max_score = float(sec.get("max_score"))
                        except Exception:  # noqa: BLE001
                            max_score = None
                    if idx == 1 and sec.get("comment") is not None:
                        main_comment = str(sec.get("comment"))

                valid_scores = [v for v in scores_by_model.values() if isinstance(v, float)]
                if valid_scores:
                    mean_dim = round(float(statistics.mean(valid_scores)), 2)
                    span = round(float(max(valid_scores) - min(valid_scores)), 2) if len(valid_scores) >= 2 else 0.0
                    participants = len(valid_scores)
                else:
                    mean_dim = None
                    span = None
                    participants = 0

                sheet_dimensions.append(
                    [
                        file_name,
                        student_id,
                        student_name,
                        dim_name,
                        mean_dim,
                        max_score,
                        *[scores_by_model.get(idx) for idx in range(1, model_count + 1)],
                        participants,
                        span,
                        main_comment,
                    ]
                )
                wrote_dim_rows = True

                # 细则明细：逐细则对齐并汇总
                items_by_model: dict[int, list[dict[str, Any]]] = {}
                for idx in range(1, model_count + 1):
                    sec = next((s for s in sections_by_model.get(idx, []) if str(s.get("name")) == dim_name), None)
                    if not isinstance(sec, dict):
                        items_by_model[idx] = []
                        continue
                    items = sec.get("items")
                    if not isinstance(items, list):
                        items_by_model[idx] = []
                        continue
                    items_by_model[idx] = [it for it in items if isinstance(it, dict) and it.get("name")]

                item_names: set[str] = set()
                for idx in range(1, model_count + 1):
                    for it in items_by_model.get(idx, []):
                        item_names.add(str(it.get("name")))

                for item_name in sorted(item_names):
                    item_scores_by_model: dict[int, Optional[float]] = {idx: None for idx in range(1, model_count + 1)}
                    item_max: Optional[float] = None
                    item_comment_main: Optional[str] = None
                    for idx in range(1, model_count + 1):
                        it = next((x for x in items_by_model.get(idx, []) if str(x.get("name")) == item_name), None)
                        if not isinstance(it, dict):
                            continue
                        try:
                            item_scores_by_model[idx] = float(it.get("score")) if it.get("score") is not None else None
                        except Exception:  # noqa: BLE001
                            item_scores_by_model[idx] = None
                        if item_max is None and it.get("max_score") is not None:
                            try:
                                item_max = float(it.get("max_score"))
                            except Exception:  # noqa: BLE001
                                item_max = None
                        if idx == 1 and it.get("comment") is not None:
                            item_comment_main = str(it.get("comment"))

                    valid_item_scores = [v for v in item_scores_by_model.values() if isinstance(v, float)]
                    if valid_item_scores:
                        mean_item = round(float(statistics.mean(valid_item_scores)), 2)
                        span_item = round(float(max(valid_item_scores) - min(valid_item_scores)), 2) if len(valid_item_scores) >= 2 else 0.0
                        participants_item = len(valid_item_scores)
                    else:
                        mean_item = None
                        span_item = None
                        participants_item = 0

                    sheet_criteria.append(
                        [
                            file_name,
                            student_id,
                            student_name,
                            dim_name,
                            item_name,
                            mean_item,
                            item_max,
                            *[item_scores_by_model.get(idx) for idx in range(1, model_count + 1)],
                            participants_item,
                            span_item,
                            item_comment_main,
                        ]
                    )

            if wrote_dim_rows:
                sheet_dimensions.append([" "] + [None] * (sheet_dimensions.max_column - 1))
                sheet_criteria.append([" "] + [None] * (sheet_criteria.max_column - 1))

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
