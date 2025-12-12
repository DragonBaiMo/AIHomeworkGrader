"""
批改业务服务，实现上传、解析、模型调用与导出闭环。
"""
from __future__ import annotations

import statistics
import json
from pathlib import Path
from typing import Iterable, List

from fastapi import UploadFile

from app.model.schemas import GradeConfig, GradeItem, GradeResponse
from app.service.ai_client import AIClient, ModelError
from app.service.prompt_builder import build_system_prompt, build_user_prompt
from app.service.prompt_config import load_prompt_config
from app.service.rules import AssignmentCategory, detect_assignment_category, get_rule
from app.util.excel_utils import ExcelExporter
from app.util.file_utils import (
    FileMeta,
    parse_filename_meta,
    generate_batch_id,
    parse_file_text,
    save_upload_files,
    validate_docx_format,
    validate_supported_file,
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
        prompt_config = load_prompt_config()

        grade_items: List[GradeItem] = []
        error_rows: List[dict] = []
        for file_path in stored_paths:
            try:
                validate_supported_file(file_path)
                meta: FileMeta = parse_filename_meta(file_path.name)
                category: AssignmentCategory = detect_assignment_category(file_path.name, config.template)
                rule = get_rule(category)
                content = parse_file_text(file_path, min_length=rule.min_length)
                student_id = meta.student_id
                student_name = meta.student_name
                raw_length = len(content)

                # 提示词编译（低代码：由 UI 配置驱动）
                if prompt_config is None or category not in prompt_config.categories:
                    raise ValueError("未找到对应分类的评分规则配置，请先在“评分规则”页面配置并保存。")
                category_cfg = prompt_config.categories[category]
                if file_path.suffix.lower() == ".docx" and not config.skip_format_check and category_cfg.docx_validation.enabled:
                    validate_docx_format(
                        file_path,
                        allowed_font_keywords=category_cfg.docx_validation.allowed_font_keywords,
                        allowed_font_size_pts=category_cfg.docx_validation.allowed_font_size_pts,
                        font_size_tolerance=category_cfg.docx_validation.font_size_tolerance,
                        target_line_spacing=category_cfg.docx_validation.target_line_spacing,
                        line_spacing_tolerance=category_cfg.docx_validation.line_spacing_tolerance,
                    )
                user_prompt, expected = build_user_prompt(category_cfg, score_target_max=float(config.score_target_max))
                system_prompt = build_system_prompt(prompt_config.system_prompt)

                model_result = await ai_client.grade(
                    content=content,
                    system_prompt=system_prompt,
                    template=user_prompt,
                    expected=expected,
                    score_target_max=float(config.score_target_max),
                )

                detail_json = json.dumps(model_result, ensure_ascii=False)
                grade_items.append(
                    GradeItem(
                        file_name=file_path.name,
                        student_id=student_id,
                        student_name=student_name,
                        score=model_result.get("score"),
                        score_rubric_max=model_result.get("score_rubric_max"),
                        score_rubric=model_result.get("score_rubric"),
                        detail_json=detail_json,
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
                        score_rubric_max=None,
                        score_rubric=None,
                        detail_json=None,
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
                        score_rubric_max=None,
                        score_rubric=None,
                        detail_json=None,
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
