"""
SQLite 数据访问层

表结构：
  questions       — 面试题目
  code_references  — 关联的知识库文档引用
  crawl_log        — 爬取日志
"""

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.core.config import settings


# ============================================================
# 数据库连接管理
# ============================================================

def get_connection() -> sqlite3.Connection:
    """获取数据库连接（自动创建 data 目录和表）"""
    db_path = Path(settings.sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # 更好的并发读
    conn.execute("PRAGMA foreign_keys=ON")
    _ensure_tables(conn)
    return conn


def _ensure_tables(conn: sqlite3.Connection):
    """建表（幂等，首次调用自动创建）"""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            difficulty TEXT NOT NULL CHECK(difficulty IN ('easy', 'medium', 'hard')),
            company TEXT,
            category TEXT NOT NULL,
            hint TEXT NOT NULL DEFAULT '',
            answer TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'nowcoder' CHECK(source IN ('local', 'nowcoder')),
            source_url TEXT,
            expected_keywords TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(title, source_url)
        );

        CREATE TABLE IF NOT EXISTS code_references (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            repo_name TEXT NOT NULL,
            repo_url TEXT NOT NULL,
            file_path TEXT NOT NULL,
            line_range TEXT NOT NULL DEFAULT 'L1',
            code_snippet TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS crawl_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL DEFAULT 'nowcoder',
            pages_crawled INTEGER NOT NULL DEFAULT 0,
            new_items INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'success',
            error_message TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);
        CREATE INDEX IF NOT EXISTS idx_questions_company ON questions(company);
        CREATE INDEX IF NOT EXISTS idx_questions_category ON questions(category);
        CREATE INDEX IF NOT EXISTS idx_questions_source ON questions(source);
        CREATE INDEX IF NOT EXISTS idx_code_refs_question ON code_references(question_id);
    """)


# ============================================================
# 题目 CRUD
# ============================================================

def list_questions(
    difficulty: Optional[str] = None,
    company: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    source: Optional[str] = None,
    page: int = 1,
    page_size: int = 12,
) -> tuple[list[dict], int]:
    """分页查询题目列表"""
    conn = get_connection()
    conditions = []
    params: list = []

    if difficulty:
        conditions.append("difficulty = ?")
        params.append(difficulty)
    if company:
        conditions.append("company = ?")
        params.append(company)
    if category:
        conditions.append("category = ?")
        params.append(category)
    if source:
        conditions.append("source = ?")
        params.append(source)
    if search:
        conditions.append("(title LIKE ? OR answer LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    # 总数
    count_sql = f"SELECT COUNT(*) FROM questions {where}"
    total = conn.execute(count_sql, params).fetchone()[0]

    # 分页数据 — 有搜索词时按相关性排序（标题命中 > 答案命中），否则按 id 倒序
    offset = (page - 1) * page_size
    if search:
        order = "ORDER BY (CASE WHEN title LIKE ? THEN 2 WHEN answer LIKE ? THEN 1 ELSE 0 END) DESC, id DESC"
        order_params = [f"%{search}%", f"%{search}%"]
    else:
        order = "ORDER BY id DESC"
        order_params = []
    data_sql = f"SELECT * FROM questions {where} {order} LIMIT ? OFFSET ?"
    rows = conn.execute(data_sql, params + order_params + [page_size, offset]).fetchall()

    conn.close()
    return [_row_to_dict(r) for r in rows], total


def get_question(qid: int) -> Optional[dict]:
    """获取单题详情（含代码引用）"""
    conn = get_connection()
    q_row = conn.execute("SELECT * FROM questions WHERE id = ?", (qid,)).fetchone()
    if not q_row:
        conn.close()
        return None

    refs = conn.execute(
        "SELECT * FROM code_references WHERE question_id = ?", (qid,)
    ).fetchall()

    result = _row_to_dict(q_row)
    result["references"] = [_row_to_dict(r) for r in refs]
    conn.close()
    return result


def get_questions_by_difficulty(difficulty: Optional[str] = None) -> list[dict]:
    """按难度获取题目列表"""
    questions, _ = list_questions(difficulty=difficulty, page=1, page_size=1000)
    return questions


def insert_question(data: dict) -> int:
    """
    插入题目（source_url 去重）
    返回新 id，如果已存在返回 None
    """
    conn = get_connection()
    source_url = data.get("source_url")

    if source_url:
        existing = conn.execute(
            "SELECT id FROM questions WHERE title = ? AND source_url = ?",
            (data["title"], source_url),
        ).fetchone()
        if existing:
            conn.close()
            return None  # 去重

    cursor = conn.execute(
        """
        INSERT INTO questions (title, difficulty, company, category, hint, answer,
                               source, source_url, expected_keywords)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["title"],
            data.get("difficulty", "medium"),
            data.get("company"),
            data.get("category", "通用"),
            data.get("hint", ""),
            data.get("answer", ""),
            data.get("source", "nowcoder"),
            source_url,
            json.dumps(data.get("expected_keywords", []), ensure_ascii=False),
        ),
    )
    conn.commit()
    qid = cursor.lastrowid
    conn.close()
    return qid


def update_question(qid: int, data: dict) -> bool:
    """
    Update question fields. Only fields present in data are updated.
    Returns True on success, False if question not found.
    """
    allowed = {
        "title", "difficulty", "company", "category",
        "hint", "answer", "source", "source_url", "expected_keywords",
    }
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return False

    if "expected_keywords" in updates and not isinstance(updates["expected_keywords"], str):
        updates["expected_keywords"] = json.dumps(updates["expected_keywords"], ensure_ascii=False)

    updates["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [qid]

    conn = get_connection()
    cursor = conn.execute(f"UPDATE questions SET {set_clause} WHERE id = ?", values)
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected


def delete_question(qid: int) -> bool:
    """
    Delete a question and its associated code references (CASCADE).
    Returns True on success, False if question not found.
    """
    conn = get_connection()
    cursor = conn.execute("DELETE FROM questions WHERE id = ?", (qid,))
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected


def get_filter_options() -> dict:
    """获取筛选选项（去重后的难度/公司/标签列表）"""
    conn = get_connection()
    difficulties = [r[0] for r in conn.execute(
        "SELECT DISTINCT difficulty FROM questions ORDER BY difficulty"
    ).fetchall()]
    companies = [r[0] for r in conn.execute(
        "SELECT DISTINCT company FROM questions WHERE company IS NOT NULL ORDER BY company"
    ).fetchall()]
    categories = [r[0] for r in conn.execute(
        "SELECT DISTINCT category FROM questions ORDER BY category"
    ).fetchall()]
    conn.close()
    return {
        "difficulties": difficulties,
        "companies": companies,
        "categories": categories,
    }


def get_stats() -> dict:
    """题库统计"""
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    by_difficulty = {
        row[0]: row[1]
        for row in conn.execute(
            "SELECT difficulty, COUNT(*) FROM questions GROUP BY difficulty"
        ).fetchall()
    }
    by_source = {
        row[0]: row[1]
        for row in conn.execute(
            "SELECT source, COUNT(*) FROM questions GROUP BY source"
        ).fetchall()
    }
    last_crawl = conn.execute(
        "SELECT * FROM crawl_log ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    return {
        "total": total,
        "by_difficulty": by_difficulty,
        "by_source": by_source,
        "last_crawl": _row_to_dict(last_crawl) if last_crawl else None,
    }


# ============================================================
# 代码引用 CRUD
# ============================================================

def insert_reference(data: dict):
    """插入代码引用"""
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO code_references (question_id, repo_name, repo_url, file_path,
                                      line_range, code_snippet, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["question_id"],
            data["repo_name"],
            data["repo_url"],
            data["file_path"],
            data.get("line_range", "L1"),
            data.get("code_snippet", ""),
            data.get("description", ""),
        ),
    )
    conn.commit()
    conn.close()


# ============================================================
# 爬取日志
# ============================================================

def log_crawl(source: str, pages: int, new_items: int, status: str = "success",
               error: Optional[str] = None):
    """记录爬取日志"""
    conn = get_connection()
    conn.execute(
        "INSERT INTO crawl_log (source, pages_crawled, new_items, status, error_message) "
        "VALUES (?, ?, ?, ?, ?)",
        (source, pages, new_items, status, error),
    )
    conn.commit()
    conn.close()


# ============================================================
# 工具函数
# ============================================================

def _row_to_dict(row: sqlite3.Row) -> dict:
    """sqlite3.Row → 普通 dict，自动反序列化 JSON 字段"""
    d = dict(row)
    if "expected_keywords" in d and isinstance(d["expected_keywords"], str):
        try:
            d["expected_keywords"] = json.loads(d["expected_keywords"])
        except json.JSONDecodeError:
            d["expected_keywords"] = []
    return d
