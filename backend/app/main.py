"""
FastAPI 应用入口
"""

from pathlib import Path
import os

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.interview import app
from app.core.config import settings

# CORS — 从配置读取允许的域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """应用启动：确保数据库已初始化，自动导入本地面经（首次）"""
    from app.core.database import get_connection, get_stats
    conn = get_connection()
    stats = get_stats()
    print(f"[startup] SQLite initialized: {settings.sqlite_path}")
    print(f"[startup] Questions in DB: {stats['total']}")

    # 首次启动如果题库为空，自动导入本地面经
    if stats["total"] == 0:
        print("[startup] 题库为空，自动导入本地面经...")
        from app.scripts.import_local_mianjing import main as import_mianjing
        import_mianjing()

    conn.close()


# ─── 部署模式：后端同时托管前端静态文件 ────────────────────
# 仅在无 Nginx 的环境下使用（开发/简单部署）
# 生产环境建议 Nginx 反向代理
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
SERVE_STATIC = os.getenv("SERVE_STATIC", "false").lower() in ("1", "true", "yes")

if SERVE_STATIC and FRONTEND_DIST.exists():
    print(f"[startup] Serving static files from: {FRONTEND_DIST}")

    # 先挂载子目录（/assets 等），再挂载根路径
    for sub in FRONTEND_DIST.iterdir():
        if sub.is_dir():
            app.mount(f"/{sub.name}", StaticFiles(directory=str(sub)), name=f"static-{sub.name}")

    # favicon 等根目录文件
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")
