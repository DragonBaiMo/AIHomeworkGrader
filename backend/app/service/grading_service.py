"""
批改业务服务，实现上传、解析、模型调用与导出闭环。
"""
from __future__ import annotations

import asyncio
import statistics
import json
import time
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.parse import urlsplit

from fastapi import UploadFile

from app.model.schemas import GradeConfig, GradeItem, GradeResponse, ModelEndpoint
from app.service.ai_client import AIClient, ModelError
from app.service.prompt_builder import build_system_prompt, build_user_prompt
from app.service.prompt_config import load_prompt_config
from app.service.rules import AssignmentCategory, detect_assignment_category, get_rule
from app.util.audit_logger import AuditLogger
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


_FILE_SEMAPHORE = asyncio.Semaphore(5)
_MODEL_SEMAPHORES: dict[str, asyncio.Semaphore] = {}
_MODEL_SEMAPHORES_LOCK = asyncio.Lock()


async def _get_model_semaphore(api_url: str) -> asyncio.Semaphore:
    raw = (api_url or "").strip()
    if not raw:
        key = "mock"
    else:
        parts = urlsplit(raw)
        if parts.scheme and parts.netloc:
            key = f"{parts.scheme.lower()}://{parts.netloc.lower()}"
        else:
            key = raw.lower()
    async with _MODEL_SEMAPHORES_LOCK:
        sem = _MODEL_SEMAPHORES.get(key)
        if sem is None:
            sem = asyncio.Semaphore(2)
            _MODEL_SEMAPHORES[key] = sem
        return sem


class GradingService:
    """批改服务，负责协调整个批次处理流程。"""

    def __init__(self) -> None:
        self.upload_root = UPLOAD_DIR

    @staticmethod
    def _resolve_model_endpoints(config: GradeConfig) -> list[ModelEndpoint]:
        base = None
        if config.api_url or config.mock:
            base = ModelEndpoint(
                api_url=config.api_url or "",
                api_key=config.api_key,
                model_name=config.model_name or "demo-model",
            )
        extras = list(config.models or [])[:2]
        if base is None:
            return extras[:3]
        return [base, *extras][:3]

    @staticmethod
    def _pick_representative_result(success_results: list[dict], target_score: float) -> dict:
        best = success_results[0]
        best_gap = abs(float(best.get("score") or 0.0) - float(target_score))
        for item in success_results[1:]:
            gap = abs(float(item.get("score") or 0.0) - float(target_score))
            if gap < best_gap:
                best = item
                best_gap = gap
        return best

    async def _grade_one_model(
        self,
        *,
        model_index: int,
        endpoint: ModelEndpoint,
        mock: bool,
        content: str,
        system_prompt: str,
        user_prompt: str,
        expected: object,
        score_target_max: float,
    ) -> dict:
        ai_client = AIClient(endpoint.api_url, endpoint.api_key, endpoint.model_name, mock=mock or (not endpoint.api_url))
        sem = await _get_model_semaphore(endpoint.api_url)
        started = time.perf_counter()
        async with sem:
            try:
                raw_text, _parsed_result, normalized_result = await ai_client.grade(
                    content=content,
                    system_prompt=system_prompt,
                    template=user_prompt,
                    expected=expected,  # type: ignore[arg-type]
                    score_target_max=score_target_max,
                )
                latency_ms = int((time.perf_counter() - started) * 1000)
                return {
                    "model_index": model_index,
                    "api_url": endpoint.api_url,
                    "model_name": endpoint.model_name,
                    "status": "success",
                    "score": normalized_result.get("score"),
                    "score_rubric": normalized_result.get("score_rubric"),
                    "score_rubric_max": normalized_result.get("score_rubric_max"),
                    "comment": normalized_result.get("comment"),
                    "normalized_result": normalized_result,
                    "raw_response": raw_text,
                    "error_message": None,
                    "latency_ms": latency_ms,
                }
            except ModelError as exc:
                latency_ms = int((time.perf_counter() - started) * 1000)
                return {
                    "model_index": model_index,
                    "api_url": endpoint.api_url,
                    "model_name": endpoint.model_name,
                    "status": "failure",
                    "score": None,
                    "score_rubric": None,
                    "score_rubric_max": None,
                    "comment": None,
                    "normalized_result": None,
                    "raw_response": getattr(exc, "raw_response", None),
                    "error_message": str(exc),
                    "latency_ms": latency_ms,
                }

    async def process(self, files: Iterable[UploadFile], config: GradeConfig) -> GradeResponse:
        """执行批次处理，并返回标准化响应。"""
        batch_id = generate_batch_id()
        batch_dir, stored_paths = save_upload_files(batch_id, files)
        exporter = ExcelExporter(batch_dir)
        prompt_config = load_prompt_config()
        auditor = AuditLogger(batch_id)
        model_endpoints = self._resolve_model_endpoints(config)
        auditor.save_meta(
            {
                "template": config.template,
                "score_target_max": float(config.score_target_max),
                "mock_mode": config.mock,
                "models": [{"api_url": m.api_url, "model_name": m.model_name} for m in model_endpoints],
                "files": [path.name for path in stored_paths],
            }
        )
        auditor.log_operation("批次初始化完成，准备开始处理文件")

        grade_items: List[GradeItem] = []
        error_rows: List[dict] = []

        async def process_one(file_path: Path) -> tuple[GradeItem, Optional[dict]]:
            async with _FILE_SEMAPHORE:
                system_prompt: str = ""
                user_prompt: str = ""
                resolved_user_prompt: str | None = None
                try:
                    validate_supported_file(file_path)
                    meta: FileMeta = parse_filename_meta(file_path.name)
                    category: AssignmentCategory = detect_assignment_category(file_path.name, config.template)
                    rule = get_rule(category)
                    content = parse_file_text(file_path, min_length=rule.min_length)
                    student_id = meta.student_id
                    student_name = meta.student_name
                    raw_length = len(content)
                    auditor.log_operation(f"开始处理文件 {file_path.name}，识别为 {category}")

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
                    auditor.save_prompts(system_prompt, user_prompt)
                    resolved_user_prompt = AIClient._build_user_content(user_prompt, content)

                    if not model_endpoints:
                        raise ValueError("未配置任何可用模型，请在设置中填写模型端点与名称。")

                    tasks = [
                        self._grade_one_model(
                            model_index=idx,
                            endpoint=endpoint,
                            mock=config.mock,
                            content=content,
                            system_prompt=system_prompt,
                            user_prompt=user_prompt,
                            expected=expected,
                            score_target_max=float(config.score_target_max),
                        )
                        for idx, endpoint in enumerate(model_endpoints, start=1)
                    ]
                    model_results = await asyncio.gather(*tasks)

                    success = [r for r in model_results if r.get("status") == "success" and r.get("score") is not None]
                    if not success:
                        errors = [str(r.get("error_message") or "未知错误") for r in model_results]
                        message = "；".join(errors[:3])
                        auditor.append_error(file_path.name, message)
                        auditor.log_operation(f"文件 {file_path.name} 所有模型均失败：{message}")
                        for r in model_results:
                            auditor.save_model_interaction(
                                file_path.name,
                                system_prompt,
                                user_prompt,
                                {},
                                model_id=f"m{r.get('model_index')}",
                                resolved_user_prompt=resolved_user_prompt,
                                raw_response=r.get("raw_response"),
                                status="failure",
                            )
                        item = GradeItem(
                            file_name=file_path.name,
                            student_id=student_id,
                            student_name=student_name,
                            score=None,
                            score_rubric_max=None,
                            score_rubric=None,
                            detail_json=None,
                            comment=None,
                            status="失败",
                            error_message=f"所有模型评分失败：{message}",
                            raw_text_length=raw_length,
                            raw_response=None,
                            aggregate_strategy="median",
                            grader_results=[
                                {
                                    "model_index": r.get("model_index"),
                                    "api_url": r.get("api_url"),
                                    "model_name": r.get("model_name"),
                                    "status": "失败",
                                    "score": r.get("score"),
                                    "comment": r.get("comment"),
                                    "error_message": r.get("error_message"),
                                    "latency_ms": r.get("latency_ms"),
                                }
                                for r in model_results
                            ],
                        )
                        return item, {"file_name": file_path.name, "error_type": "模型调用错误", "error_message": item.error_message}

                    scores_success = [float(r.get("score")) for r in success]
                    median_score = float(statistics.median(scores_success))
                    picked = self._pick_representative_result(success, median_score)
                    normalized_result = picked.get("normalized_result") or {}
                    detail_json = json.dumps(normalized_result, ensure_ascii=False)

                    for r in model_results:
                        auditor.save_model_interaction(
                            file_path.name,
                            system_prompt,
                            user_prompt,
                            (r.get("normalized_result") or {}) if r.get("status") == "success" else {},
                            model_id=f"m{r.get('model_index')}",
                            resolved_user_prompt=resolved_user_prompt,
                            raw_response=r.get("raw_response"),
                            status="success" if r.get("status") == "success" else "failure",
                        )

                    item = GradeItem(
                        file_name=file_path.name,
                        student_id=student_id,
                        student_name=student_name,
                        score=round(median_score, 2),
                        score_rubric_max=normalized_result.get("score_rubric_max"),
                        score_rubric=normalized_result.get("score_rubric"),
                        detail_json=detail_json,
                        comment=normalized_result.get("comment"),
                        status="成功",
                        error_message=None,
                        raw_text_length=raw_length,
                        raw_response=None,
                        aggregate_strategy="median",
                        grader_results=[
                            {
                                "model_index": r.get("model_index"),
                                "api_url": r.get("api_url"),
                                "model_name": r.get("model_name"),
                                "status": "成功" if r.get("status") == "success" else "失败",
                                "score": r.get("score"),
                                "comment": r.get("comment"),
                                "error_message": r.get("error_message"),
                                "latency_ms": r.get("latency_ms"),
                            }
                            for r in model_results
                        ],
                    )
                    return item, None
                except ValueError as exc:
                    logger.warning("文件处理异常：%s -> %s", file_path.name, exc)
                    auditor.append_error(file_path.name, str(exc))
                    auditor.log_operation(f"文件 {file_path.name} 处理失败：{exc}")
                    return (
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
                            raw_response=None,
                            aggregate_strategy="median",
                            grader_results=None,
                        ),
                        {"file_name": file_path.name, "error_type": "解析校验错误", "error_message": str(exc)},
                    )

        results = await asyncio.gather(*[process_one(p) for p in stored_paths])
        for item, error_row in results:
            grade_items.append(item)
            if error_row:
                error_rows.append(error_row)

        scores = [item.score for item in grade_items if item.score is not None]
        average_score = round(statistics.mean(scores), 2) if scores else None
        score_rubric_values = [item.score_rubric for item in grade_items if item.score_rubric is not None]
        average_score_rubric = round(statistics.mean(score_rubric_values), 2) if score_rubric_values else None
        rubric_max_values = sorted({float(item.score_rubric_max) for item in grade_items if item.score_rubric_max is not None})

        auditor.log_operation("批次处理完毕，准备导出 Excel 与 响应")

        exporter.export_results(
            [item.model_dump() for item in grade_items],
            summary={
                "批次ID": batch_id,
                "目标满分": float(config.score_target_max),
                "规则满分（可能多值）": " / ".join(str(v) for v in rubric_max_values) if rubric_max_values else "",
                "文件总数": len(grade_items),
                "成功数": len(scores),
                "失败数": len(grade_items) - len(scores),
                "平均分（目标满分制）": average_score if average_score is not None else "",
                "平均规则分": average_score_rubric if average_score_rubric is not None else "",
            },
            error_rows=error_rows,
        )
        exporter.export_errors(error_rows)

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
