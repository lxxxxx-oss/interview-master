#!/usr/bin/env python3
"""首次启用 FTS5 — 手动重建索引（解决 startup 时 database locked 问题）"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "questions.db"
conn = sqlite3.connect(str(DB_PATH))

# 清理旧表
conn.execute("DROP TABLE IF EXISTS questions_fts")
conn.execute("DROP TRIGGER IF EXISTS questions_ai")
conn.execute("DROP TRIGGER IF EXISTS questions_ad")
conn.execute("DROP TRIGGER IF EXISTS questions_au")
conn.commit()

# 创建 FTS5 虚拟表
conn.execute(
    "CREATE VIRTUAL TABLE questions_fts USING fts5(title, answer, hint, category, expected_keywords)"
)

# 灌入全部数据
rows = conn.execute("SELECT id, title, answer, hint, category, expected_keywords FROM questions").fetchall()
for row in rows:
    conn.execute(
        "INSERT INTO questions_fts(rowid, title, answer, hint, category, expected_keywords) VALUES (?, ?, ?, ?, ?, ?)",
        row,
    )
conn.commit()

# 验证
total = conn.execute("SELECT COUNT(*) FROM questions_fts").fetchone()[0]
print(f"FTS rows: {total}")

# 测试搜索
for q in ["agent", "RAG", "function calling", "面试"]:
    r = conn.execute(f"SELECT COUNT(*) FROM questions_fts WHERE questions_fts MATCH ?", (q,)).fetchone()[0]
    print(f"  {q}: {r}")

conn.close()
print("Done — FTS index ready")
