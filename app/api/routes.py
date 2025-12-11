"""
FastAPI 路由定义，提供健康检查、批改与下载接口。
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from app.model.schemas import GradeConfig, GradeResponse
from app.service.grading_service import GradingService
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
    api_url: str | None = None,
    api_key: str | None = None,
    model_name: str | None = None,
    template: str = "职业规划",
    mock: bool = False,
    srv: GradingService = Depends(get_service),
) -> GradeResponse:
    """接收文件并执行批改流程。"""
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一个 docx 文件")
    if not mock:
        if not api_url:
            raise HTTPException(status_code=400, detail="未填写模型接口地址")
    config = GradeConfig(api_url=api_url, api_key=api_key, model_name=model_name, template=template, mock=mock)
    logger.info("收到批改请求，文件数：%d，模板：%s，mock=%s", len(files), template, mock)
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


router_home = APIRouter()


@router_home.get("/", response_class=HTMLResponse)
async def home_page() -> HTMLResponse:
    """返回首页 HTML。"""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=500, detail="缺失前端页面文件")
    return HTMLResponse(index_file.read_text(encoding="utf-8"))


# 静态资源挂载需要在 main 中完成
