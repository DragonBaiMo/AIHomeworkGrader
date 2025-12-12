"""
FastAPI 路由定义，提供健康检查、批改与下载接口。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from app.model.schemas import GradeConfig, GradeResponse
from app.service.grading_service import GradingService
from app.service.prompt_config import PROMPT_CONFIG_PATH, load_prompt_config, save_prompt_config
from app.util.logger import logger
from config.settings import STATIC_DIR

router = APIRouter(prefix="/api")
service = GradingService()


def get_service() -> GradingService:
    """注入批改服务实例。"""
    return service


@router.get("/ping")
async def ping() -> JSONResponse:
    """健康检查接口。"""
    return JSONResponse({"message": "pong"})


@router.post("/grade", response_model=GradeResponse)
async def grade(
    files: List[UploadFile] = File(..., description="待批改的作业文件"),
    api_url: str | None = Form(default=None, description="模型接口地址"),
    api_key: str | None = Form(default=None, description="API 密钥"),
    model_name: str | None = Form(default=None, description="模型名称"),
    template: str = Form(default="auto", description="作业模板类型（auto 为自动识别，否则传分类 key）"),
    mock: str = Form(default="false", description="是否使用模拟模式"),
    skip_format_check: str = Form(default="false", description="是否跳过格式检查"),
    score_target_max: float = Form(default=60.0, description="目标满分（用于将评分规则总分按比例换算）"),
    srv: GradingService = Depends(get_service),
) -> GradeResponse:
    """接收文件并执行批改流程。"""
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一个作业文件（.docx/.md/.markdown/.txt）")
    # 前端 FormData 传递布尔值为字符串，需要转换
    is_mock = mock.lower() == "true"
    is_skip_format = skip_format_check.lower() == "true"
    if score_target_max <= 0:
        raise HTTPException(status_code=400, detail="目标满分必须大于 0")
    if not is_mock:
        if not api_url:
            raise HTTPException(status_code=400, detail="未填写模型接口地址")
    config = GradeConfig(
        api_url=api_url,
        api_key=api_key,
        model_name=model_name,
        template=template,
        mock=is_mock,
        skip_format_check=is_skip_format,
        score_target_max=score_target_max,
    )
    logger.info("收到批改请求：文件数=%d，模板=%s，模拟模式=%s，跳过格式检查=%s", len(files), template, is_mock, is_skip_format)
    return await srv.process(files, config)


@router.get("/download/{file_type}/{batch_id}")
async def download(file_type: str, batch_id: str, srv: GradingService = Depends(get_service)) -> FileResponse:
    """提供成绩表或异常清单的下载。"""
    try:
        path: Path = srv.get_download_path(batch_id, file_type)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="未找到对应批次文件")
    if not path.exists():
        raise HTTPException(status_code=404, detail="文件尚未生成或已被清理")
    filename = path.name
    return FileResponse(path, filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/prompt-config")
async def get_prompt_config() -> JSONResponse:
    """返回当前提示词配置（用于前端低代码编辑）。"""
    config = load_prompt_config()
    if config is None:
        return JSONResponse({"config": None})
    raw = json.loads(PROMPT_CONFIG_PATH.read_text(encoding="utf-8"))
    return JSONResponse({"config": raw})


@router.post("/prompt-config")
async def update_prompt_config(payload: dict = Body(...)) -> JSONResponse:
    """更新提示词配置并同步到 Markdown。"""
    try:
        save_prompt_config(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse({"message": "提示词配置已更新"})


@router.post("/prompt-preview")
async def prompt_preview(payload: dict = Body(...)) -> JSONResponse:
    """返回提示词预览（用于前端低代码编辑即时检查）。"""
    from app.service.prompt_builder import build_system_prompt, build_user_prompt
    from app.service.prompt_config import parse_prompt_config

    try:
        cfg = parse_prompt_config(payload.get("prompt_config") or {})
        category_key = str(payload.get("category_key") or "").strip()
        score_target_max = float(payload.get("score_target_max") or 60.0)
        if not category_key:
            raise ValueError("category_key 不能为空")
        cat_cfg = cfg.categories.get(category_key)
        if cat_cfg is None:
            raise ValueError("未找到对应分类配置")
        user_prompt, expected = build_user_prompt(cat_cfg, score_target_max=score_target_max)
        system_prompt = build_system_prompt(cfg.system_prompt)
        return JSONResponse(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "score_rubric_max": expected.rubric_max,
                "score_target_max": score_target_max,
            }
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


router_home = APIRouter()


@router_home.get("/", response_class=HTMLResponse)
async def home_page() -> HTMLResponse:
    """返回首页 HTML。"""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=500, detail="缺失前端页面文件")
    return HTMLResponse(index_file.read_text(encoding="utf-8"))


# 静态资源挂载需要在 main 中完成
