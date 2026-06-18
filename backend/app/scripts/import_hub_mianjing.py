#!/usr/bin/env python
"""
Import interview questions from agent-interview-hub-main.

Source directory structure:
    agent-interview-hub-main/
    ├── <Company>/面试题与面经.md    # Q&A pairs with ### Q: markers
    ├── 通用知识/高频面试新题-2025.md  # Also ### Q: markers

Usage:
    python -m app.scripts.import_hub_mianjing
    python -m app.scripts.import_hub_mianjing --dry-run
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.core.database import get_connection, insert_question


HUB_PATH = Path("C:/Users/Lesedi/Desktop/agent-interview-hub-main/agent-interview-hub-main")

# Which companies have 面试题与面经.md
COMPANY_DIRS = [
    "OpenAI", "初创公司", "华为", "商汤科技", "字节跳动",
    "小红书", "微软", "快手", "百度", "美团", "腾讯",
    "蚂蚁集团", "谷歌", "阿里巴巴",
]

# Additional files to parse
EXTRA_FILES = [
    "通用知识/高频面试新题-2025.md",
]


def parse_questions_from_md(md_path: Path) -> list[dict]:
    """Parse ### Q: ... **参考答案：** ... blocks from a markdown file."""
    if not md_path.exists():
        print(f"  [WARN] File not found: {md_path}")
        return []

    text = md_path.read_text(encoding="utf-8")
    questions = []

    # Split on ### Q: markers
    chunks = re.split(r"\n### Q:\s*", text)

    for chunk in chunks[1:]:  # skip content before first ### Q:
        lines = chunk.split("\n")
        title = lines[0].strip()

        # Find the answer section - look for **参考答案：** marker
        answer_lines = []
        answer_started = False
        hint = ""

        for line in lines[1:]:
            # Capture thinking hint
            if "💡 思考逻辑" in line or "**💡" in line:
                hint_part = line.strip().lstrip("**").rstrip("**").strip()
                if hint_part:
                    hint = hint_part
                continue

            if "**参考答案：**" in line or "**参考答案:**" in line:
                answer_started = True
                # Capture content after the marker on same line
                remaining = re.sub(r"\*\*参考答案：[：*]*\*\*\s*", "", line)
                if remaining.strip():
                    answer_lines.append(remaining)
                continue

            if answer_started:
                # Stop at next ### section or --- marker that separates sections
                if line.strip().startswith("### ") and "Q:" in line:
                    break
                if line.strip() == "---":
                    # Not necessarily end — 阿里巴巴 uses --- within answers
                    # Only stop if it looks like a section divider (followed by ## header)
                    pass
                answer_lines.append(line)

            # Stop if we hit the next question marker
            if re.match(r"^###\s+Q:", line):
                break

        answer = "\n".join(answer_lines).strip()

        # Clean up answer: remove trailing --- if it's a separator
        answer = re.sub(r"\n---\s*$", "", answer)

        if title and answer:
            questions.append({
                "title": title,
                "answer": answer,
                "hint": hint,
            })

    return questions


def infer_difficulty(title: str, answer: str) -> str:
    """Heuristic difficulty inference."""
    text = (title + answer).lower()
    # hard signals
    hard_signals = ["架构设计", "多 agent", "安全威胁", "护城河", "定价模型",
                    "跨模型兼容", "harness", "structured output", "评测体系",
                    "pmf", "context engineering"]
    easy_signals = ["区别", "是什么", "定义", "基本概念", "基本流程", "工作原理"]

    if any(s in text for s in hard_signals):
        return "hard"
    if any(s in text for s in easy_signals):
        return "easy"
    return "medium"


def infer_category(title: str) -> str:
    """Heuristic category inference."""
    t = title.lower()
    if any(k in t for k in ["rag", "检索", "lost in the middle", "chunk", "embedding", "向量"]):
        return "RAG"
    if any(k in t for k in ["mcp", "model context protocol"]):
        return "MCP协议"
    if any(k in t for k in ["function calling", "tool use", "工具调用", "tool call"]):
        return "Function Calling"
    if any(k in t for k in ["prompt", "提示词", "context engineering", "上下文"]):
        return "Prompt Engineering"
    if any(k in t for k in ["记忆", "memory", "上下文维护"]):
        return "记忆机制"
    if any(k in t for k in ["多模型", "架构", "跨模型", "harness"]):
        return "模型架构"
    return "Agent基础"


def main(dry_run: bool = False):
    total_imported = 0
    total_skipped = 0
    all_questions = []

    # Parse company files
    for company in COMPANY_DIRS:
        md_path = HUB_PATH / company / "面试题与面经.md"
        qs = parse_questions_from_md(md_path)
        print(f"\n[{company}] {len(qs)} questions found")
        for q in qs:
            q["company"] = company
            q["category"] = infer_category(q["title"])
            q["difficulty"] = infer_difficulty(q["title"], q["answer"])
            q["source"] = "hub"
        all_questions.extend(qs)

    # Parse extra files
    for rel_path in EXTRA_FILES:
        md_path = HUB_PATH / rel_path
        company = "通用知识"
        qs = parse_questions_from_md(md_path)
        print(f"\n[{rel_path}] {len(qs)} questions found")
        for q in qs:
            q["company"] = company
            q["category"] = infer_category(q["title"])
            q["difficulty"] = infer_difficulty(q["title"], q["answer"])
            q["source"] = "hub"
        all_questions.extend(qs)

    print(f"\nTotal questions parsed: {len(all_questions)}")

    if dry_run:
        print("\n[DRY RUN] Sample of questions to import:")
        for i, q in enumerate(all_questions[:15]):
            print(f"  {i+1}. [{q['company']}] [{q['difficulty']}] [{q['category']}] {q['title'][:80]}")
        print(f"  ... and {len(all_questions) - 15} more")
        return

    # Insert into database
    for q in all_questions:
        data = {
            "title": q["title"],
            "difficulty": q["difficulty"],
            "company": q["company"],
            "category": q["category"],
            "hint": q.get("hint", ""),
            "answer": q["answer"],
            "source": q["source"],
            "source_url": None,
            "expected_keywords": [],
        }
        qid = insert_question(data)
        if qid is not None:
            total_imported += 1
        else:
            total_skipped += 1

    print(f"\nDone: {total_imported} imported, {total_skipped} skipped (duplicates)")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
