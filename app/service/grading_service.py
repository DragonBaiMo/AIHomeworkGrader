"""
批改业务服务，实现上传、解析、模型调用与导出闭环。
"""
from __future__ import annotations

import statistics
from pathlib import Path
from typing import Iterable, List

from fastapi import UploadFile

from app.model.schemas import GradeConfig, GradeItem, GradeResponse
from app.service.ai_client import AIClient, ModelError
from app.service.rules import AssignmentCategory, build_template_prompt, detect_assignment_category, get_rule
from app.util.excel_utils import ExcelExporter
from app.util.file_utils import (
    FileMeta,
    parse_filename_meta,
    generate_batch_id,
    parse_docx_text,
    save_upload_files,
    validate_docx_format,
    validate_docx,
)
from app.util.logger import logger
from config.settings import UPLOAD_DIR


class GradingService:
    """批改服务，负责协调整个批次处理流程。"""

    def __init__(self) -> None:
        self.upload_root = UPLOAD_DIR

    async def process(self, files: Iterable[UploadFile], config: GradeConfig) -> GradeResponse:
        """执行批次处理，并返回标准化响应。"""
        batch_id = generate_batch_id()
        batch_dir, stored_paths = save_upload_files(batch_id, files)
        exporter = ExcelExporter(batch_dir)
        ai_client = AIClient(config.api_url, config.api_key, config.model_name, mock=config.mock)

        grade_items: List[GradeItem] = []
        error_rows: List[dict] = []
        for file_path in stored_paths:
            try:
                validate_docx(file_path)
                if not config.skip_format_check:
                    validate_docx_format(file_path)
                meta: FileMeta = parse_filename_meta(file_path.name)
                category: AssignmentCategory = detect_assignment_category(file_path.name, config.template)
                rule = get_rule(category)
                content = parse_docx_text(file_path, min_length=rule.min_length)
                student_id = meta.student_id
                student_name = meta.student_name
                raw_length = len(content)
                template_prompt = build_template_prompt(category)
                model_result = await ai_client.grade(content, template_prompt)
                grade_items.append(
                    GradeItem(
                        file_name=file_path.name,
                        student_id=student_id,
                        student_name=student_name,
                        score=model_result.get("score"),
                        dimension_structure=model_result.get("dimension", {}).get("structure"),
                        dimension_content=model_result.get("dimension", {}).get("content"),
                        dimension_expression=model_result.get("dimension", {}).get("expression"),
                        comment=model_result.get("comment"),
                        status="成功",
                        error_message=None,
                        raw_text_length=raw_length,
                    )
                )
            except ValueError as exc:
                logger.warning("文件处理异常：%s -> %s", file_path.name, exc)
                grade_items.append(
                    GradeItem(
                        file_name=file_path.name,
                        student_id=None,
                        student_name=None,
                        score=None,
                        dimension_structure=None,
                        dimension_content=None,
                        dimension_expression=None,
                        comment=None,
                        status="失败",
                        error_message=str(exc),
                        raw_text_length=0,
                    )
                )
                error_rows.append(
                    {
                        "file_name": file_path.name,
                        "error_type": "解析校验错误",
                        "error_message": str(exc),
                    }
                )
            except ModelError as exc:
                logger.warning("模型评分失败：%s -> %s", file_path.name, exc)
                grade_items.append(
                    GradeItem(
                        file_name=file_path.name,
                        student_id=None,
                        student_name=None,
                        score=None,
                        dimension_structure=None,
                        dimension_content=None,
                        dimension_expression=None,
                        comment=None,
                        status="失败",
                        error_message=str(exc),
                        raw_text_length=0,
                    )
                )
                error_rows.append(
                    {
                        "file_name": file_path.name,
                        "error_type": "模型调用错误",
                        "error_message": str(exc),
                    }
                )

        exporter.export_results([item.model_dump() for item in grade_items])
        exporter.export_errors(error_rows)

        scores = [item.score for item in grade_items if item.score is not None]
        average_score = round(statistics.mean(scores), 2) if scores else None

        response = GradeResponse(
            batch_id=batch_id,
            total_files=len(grade_items),
            success_count=len(scores),
            error_count=len(grade_items) - len(scores),
            average_score=average_score,
            download_result_url=f"/api/download/result/{batch_id}",
            download_error_url=f"/api/download/error/{batch_id}",
            items=grade_items,
        )
        logger.info(
            "批次完成：%s，总计%d，成功%d，异常%d，平均分%s",
            batch_id,
            response.total_files,
            response.success_count,
            response.error_count,
            response.average_score,
        )
        return response

    def get_download_path(self, batch_id: str, file_type: str) -> Path:
        """根据批次与文件类型返回下载路径。"""
        batch_dir = self.upload_root / batch_id
        if file_type == "result":
            return batch_dir / "grade_result.xlsx"
        if file_type == "error":
            return batch_dir / "error_list.xlsx"
        raise FileNotFoundError("不支持的文件类型")
