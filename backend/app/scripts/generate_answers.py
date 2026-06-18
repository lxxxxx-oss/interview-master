#!/usr/bin/env python
"""
批量生成标准答案脚本 — 调用 LLM 为全题库生成详细答案

用法：
    LLM_ENABLED=true LLM_API_KEY=sk-xxx python -m app.scripts.generate_answers

选项：
    --dry-run      只打印不写入
    --limit N      只处理 N 道题（测试用）
    --batch N      每批处理 N 道题（默认 5）
"""

import sys
import json
import asyncio
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.core.config import settings
from app.core.database import get_connection


def get_questions_without_answer(batch_size: int):
    """
    生成器：逐批返回答案为空或占位文本的题目。
    每批 yield [(id, title, category, difficulty), ...]
    """
    conn = get_connection()
    all_rows = conn.execute(
        "SELECT id, title, category, difficulty, answer, source FROM questions ORDER BY id"
    ).fetchall()

    placeholders = ["答案来自牛客", "详细答案请参考", "请查看原文"]
    batch = []
    for row in all_rows:
        ans = row["answer"] or ""
        is_placeholder = any(p in ans for p in placeholders)
        if is_placeholder or len(ans) < 30:
            batch.append((row["id"], row["title"], row["category"], row["difficulty"]))
            if len(batch) >= batch_size:
                yield batch
                batch = []
    if batch:
        yield batch
    conn.close()


SYSTEM_PROMPT = """\
你是一位 AI Agent 领域的资深面试官和讲师。请为以下面试题撰写一份高质量的标准答案。

要求：
1. 使用中文，Markdown 格式
2. 结构清晰：先给出核心定义/结论（1-2句），再展开详细解释
3. 覆盖关键知识点：概念定义、核心原理、实现流程、适用场景、常见误区
4. 包含代码示例（Python 或伪代码），用 ``` 包裹
5. 涉及对比（如 A vs B）的题目，用对比表格呈现
6. 答案长度：200-800 字（easy 200-400，medium 400-600，hard 600-800）
7. 语言：专业但可读，避免翻译腔

返回格式（JSON）：
{
  "answers": [
    {"index": 1, "answer": "## 标题\\n\\n详细答案...", "keywords": ["关键词1", "关键词2"]},
    ...
  ]
}"""


def build_user_prompt(batch):
    """构建批量题目的 user prompt"""
    items = []
    for i, (qid, title, category, difficulty) in enumerate(batch, 1):
        items.append(f"{i}. [{difficulty}] [{category}] {title}")
    return "请为以下面试题撰写标准答案：\n\n" + "\n".join(items)


async def generate_batch(batch):
    """调用 LLM 为一组题目生成答案，返回 [(qid, answer, keywords), ...]"""
    from app.core.llm_client import LlmClient, _parse_json

    client = LlmClient()
    if not client.is_available:
        print("ERROR: LLM 不可用。请设置 LLM_ENABLED=true LLM_API_KEY=sk-xxx")
        return []

    user_prompt = build_user_prompt(batch)
    text = await client.chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
        max_tokens=4096,
    )

    if text is None:
        print(f"ERROR: LLM 返回 None")
        return []

    parsed = _parse_json(text)

    # ─── 宽松解析：JSON 截断/格式错误时，逐个 rescue ───
    if isinstance(parsed, dict) and "answers" in parsed:
        answers_list = parsed["answers"]
        if not isinstance(answers_list, list):
            answers_list = [answers_list]
    else:
        # 无法解析整体，逐个 fallback 到单题重试
        print(f"WARN: 批量解析失败，逐个降级重试: {text[:200]}")
        answers_list = []

    # 按 index 建立映射（已解析成功的部分）
    by_index = {}
    for item in answers_list:
        if isinstance(item, dict):
            by_index[item.get("index", 0)] = item

    results = []
    for i, (qid, title, category, difficulty) in enumerate(batch, 1):
        item = by_index.get(i, {})
        answer_text = item.get("answer", "")
        keywords = item.get("keywords", [])

        if not answer_text or len(answer_text) < 20:
            # 逐个降级重试
            print(f"  ↻ Q{qid} 单独重试…")
            single_result = await generate_single(client, title, category, difficulty)
            if single_result:
                answer_text = single_result[0]
                keywords = single_result[1]

        if answer_text and len(answer_text) >= 20:
            results.append((qid, answer_text, keywords))
        else:
            results.append((
                qid,
                f"## {title}\n\n该题目涉及 {category} 领域的核心知识点，请参考相关文档和面经获取详细答案。",
                [],
            ))

    return results


async def generate_single(client, title: str, category: str, difficulty: str):
    """单题生成（batch 中某题失败时的 fallback）"""
    prompt = f"[{difficulty}] [{category}] {title}"
    # 用更简单的 prompt，减少 JSON 格式要求
    text = await client.chat_completion(
        messages=[
            {"role": "system", "content": "你是 AI Agent 领域面试专家。请为以下题目撰写一份标准答案。答案用中文 Markdown 格式，包含核心概念解释、实现细节、代码示例（用 ``` 包裹）、适用场景和常见误区。标题用 ##。长度 200-600 字。直接输出 Markdown，不要输出 JSON 或其他格式。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        max_tokens=2048,
    )
    if text and len(text.strip()) >= 30:
        return text.strip(), []
    return None


def update_database(results, dry_run=False):
    """将生成的答案写入 SQLite"""
    conn = get_connection()
    updated = 0

    for qid, answer, keywords in results:
        kw_json = json.dumps(keywords, ensure_ascii=False) if keywords else None
        if dry_run:
            print(f"  [DRY-RUN] Q{qid}: answer={len(answer)}chars, keywords={len(keywords) if keywords else 0}")
            updated += 1
            continue

        if kw_json:
            conn.execute(
                "UPDATE questions SET answer = ?, expected_keywords = ?, updated_at = datetime('now') WHERE id = ?",
                (answer, kw_json, qid),
            )
        else:
            conn.execute(
                "UPDATE questions SET answer = ?, updated_at = datetime('now') WHERE id = ?",
                (answer, qid),
            )
        updated += 1

    conn.commit()
    conn.close()
    return updated


async def main_async(dry_run=False, limit=0, batch_size=5):
    total_processed = 0
    total_updated = 0

    for batch in get_questions_without_answer(batch_size):
        if limit and total_processed >= limit:
            break
        if limit:
            remaining = limit - total_processed
            batch = batch[:remaining]

        ids = [q[0] for q in batch]
        titles = [q[1][:40] for q in batch]
        print(f"\n处理中: IDs={ids} → {titles}")

        results = await generate_batch(batch)
        if results:
            n = update_database(results, dry_run=dry_run)
            total_updated += n
            for qid, ans, kw in results:
                print(f"  ✓ Q{qid}: answer={len(ans)}chars, keywords={len(kw) if kw else 0}")
        else:
            print(f"  ✗ 失败")

        total_processed += len(batch)
        # 请求间停顿避免限流
        await asyncio.sleep(1)

    print(f"\n{'='*50}")
    print(f"完成: 处理 {total_processed} 题, 更新 {total_updated} 题")
    if dry_run:
        print("  (DRY-RUN 模式，未实际写入)")


def main():
    parser = argparse.ArgumentParser(description="批量生成面试题标准答案")
    parser.add_argument("--dry-run", action="store_true", help="只打印不写入")
    parser.add_argument("--limit", type=int, default=0, help="最多处理 N 道题")
    parser.add_argument("--batch", type=int, default=5, help="每批处理题数")
    args = parser.parse_args()

    if not settings.llm_enabled:
        print("请先设置 LLM_ENABLED=true")
        sys.exit(1)
    if not settings.llm_api_key:
        print("请先设置 LLM_API_KEY")
        sys.exit(1)

    asyncio.run(main_async(dry_run=args.dry_run, limit=args.limit, batch_size=args.batch))


if __name__ == "__main__":
    main()
