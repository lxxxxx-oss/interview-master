"""
集中配置模块 — 所有环境相关参数统一从这里读取

使用方法：
    from app.core.config import settings
    db_path = settings.sqlite_path
"""

import os
from pathlib import Path


class Settings:
    """从环境变量读取配置，提供合理默认值"""

    # ─── 项目路径 ─────────────────────────────────
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent  # backend/
    DATA_DIR: Path = PROJECT_ROOT / "data"

    # ─── SQLite ────────────────────────────────────
    @property
    def sqlite_path(self) -> str:
        """SQLite 数据库文件路径。Docker 部署时挂载 volume 到此路径父目录。"""
        return os.getenv(
            "SQLITE_PATH",
            str(self.DATA_DIR / "questions.db"),
        )

    @property
    def sqlite_url(self) -> str:
        return f"sqlite:///{self.sqlite_path}"

    # ─── 服务器 ────────────────────────────────────
    @property
    def host(self) -> str:
        return os.getenv("HOST", "0.0.0.0")

    @property
    def port(self) -> int:
        return int(os.getenv("PORT", "8000"))

    # ─── CORS — 生产环境通过环境变量追加域名 ────────
    @property
    def cors_origins(self) -> list[str]:
        raw = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        )
        return [o.strip() for o in raw.split(",") if o.strip()]

    # ─── Playwright 爬虫配置 ───────────────────────
    @property
    def crawl_delay_seconds(self) -> float:
        """牛客网请求间隔（秒），避免被 ban"""
        return float(os.getenv("CRAWL_DELAY", "2.0"))

    @property
    def crawl_max_pages(self) -> int:
        """每次爬取最多翻多少页"""
        return int(os.getenv("CRAWL_MAX_PAGES", "5"))

    @property
    def nowcoder_cookie(self) -> str | None:
        """牛客网登录 Cookie（可选，部分面经需要登录才能看全文）"""
        return os.getenv("NOWCODER_COOKIE", None)

    # ─── 本地面经路径（过渡期用，后续移除） ────────
    @property
    def local_mianjing_path(self) -> str:
        return os.getenv(
            "LOCAL_MIANJING_PATH",
            "C:/Users/Lesedi/Desktop/Typora笔记/面经/Agent面经.md",
        )

    # ─── 调试 ──────────────────────────────────────
    @property
    def debug(self) -> bool:
        return os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")

    # ─── LLM ───────────────────────────────────────
    @property
    def llm_enabled(self) -> bool:
        """LLM 总开关：false 时所有 LLM 调用回退到启发式"""
        return os.getenv("LLM_ENABLED", "false").lower() in ("1", "true", "yes")

    @property
    def llm_api_key(self) -> str | None:
        return os.getenv("LLM_API_KEY", None)

    @property
    def llm_base_url(self) -> str:
        return os.getenv("LLM_BASE_URL", "https://apihub.agnes-ai.com/v1")

    @property
    def llm_model(self) -> str:
        return os.getenv("LLM_MODEL", "agnes-2.0-flash")

    @property
    def llm_temperature(self) -> float:
        return float(os.getenv("LLM_TEMPERATURE", "0.3"))

    @property
    def llm_max_tokens(self) -> int:
        return int(os.getenv("LLM_MAX_TOKENS", "4096"))


settings = Settings()
