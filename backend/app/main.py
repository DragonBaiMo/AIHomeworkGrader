"""
应用入口，组装 FastAPI 应用并挂载路由与静态资源。
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router, router_home
from config.settings import STATIC_DIR, ensure_directories
from app.util.logger import logger

ensure_directories()

app = FastAPI(title="AI 作业批改工具", description="提供批量 docx 批改与导出能力", version="0.1.0")

# CORS 设置，便于本地调试
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_home)
app.include_router(router)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.on_event("startup")
async def startup_event() -> None:
    """启动钩子，记录启动日志。"""
    logger.info("AI 作业批改工具启动成功。")


@app.get("/health")
async def health() -> dict[str, str]:
    """备用健康检查接口。"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
