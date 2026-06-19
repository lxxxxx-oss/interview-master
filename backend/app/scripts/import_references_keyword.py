#!/usr/bin/env python
"""
知识库引用关键词匹配脚本 — 用题目标题+答案+分类中的关键词
匹配知识库文件的描述文本，选 Top-K 最相关的文件关联到题目。

替代原来的「同类全关联」方案，减少噪音。
"""

import sys, re
from pathlib import Path
from collections import Counter
from typing import Set, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.core.database import get_connection, insert_reference
from app.scripts.import_references import KNOWLEDGE_BASES, clear_references


# ═══════════════════════════════════════════════════════════════
# 关键词库 — 每个技术主题的匹配词
# ═══════════════════════════════════════════════════════════════

KEYWORD_MAP = {
    "RAG": [
        "RAG", "检索增强", "检索", "chunk", "切片", "嵌入", "embedding",
        "向量数据库", "Milvus", "FAISS", "Chroma", "知识库", "文档解析",
        "数据加载", "索引优化", "ANN", "召回", "retrieval", "knowledge",
    ],
    "Agent基础": [
        "Agent", "智能体", "agent loop", "ReAct", "Plan-and-Solve",
        "Reflection", "Multi-Agent", "协作", "routing", "并行",
        "Parallelization", "Prompt Chaining", "编排", "状态机",
        "规划", "Planning", "决策", "工作流", "workflow", "harness",
        "Worktree", "隔离", "并发", "生命周期", "loop", "低代码",
    ],
    "MCP协议": [
        "MCP", "Model Context Protocol", "上下文协议", "plugin",
        "工具注册", "Server", "动态发现", "接口", "协议",
    ],
    "Function Calling": [
        "Function Call", "工具调用", "Tool Use", "tool call",
        "函数调用", "分发", "参数解析", "external tool", "API",
    ],
    "记忆机制": [
        "记忆", "memory", "Memory", "上下文", "context", "session",
        "对话历史", "持久化", "存储", "检索", "短期记忆", "长期记忆",
        "Learning", "Adaptation", "反馈", "衰减",
    ],
    "Prompt Engineering": [
        "Prompt", "提示词", "提示链", "Chain", "CoT", "ToT",
        "推理", "指令", "引导", "模板", "措辞",
    ],
    "模型架构": [
        "模型", "LLM", "Transformer", "模型切换", "路由", "Router",
        "跨模型", "兼容", "抽象层", "适配", "能力探测", "降级",
        "架构", "模型架构", "引擎", "运行时", "inference",
    ],
    "向量检索": [
        "向量", "embedding", "嵌入", "相似度", "ANN", "KNN",
        "索引", "FAISS", "Milvus", "Chroma", "pgvector",
        "distance", "cosine", "距离", "检索",
    ],
}


def tokenize(text: str) -> Set[str]:
    """从文本中提取有意义的关键词"""
    text = text.lower()
    tokens = set()
    # 中文无空格分词简单处理：按常见技术词匹配
    for cat_keywords in KEYWORD_MAP.values():
        for kw in cat_keywords:
            if kw.lower() in text:
                tokens.add(kw.lower())
    return tokens


def compute_match_score(
    question_title: str,
    question_answer: str,
    question_category: str,
    file_description: str,
    file_path: str,
    kb_description: str,
) -> float:
    """
    综合评分：题目标题(30%) + 答案(30%) + 文件描述(30%) + 分类权重(10%)

    用答案全文而非仅前 500 字符，捕获更多语义信号。
    """
    title_tokens = tokenize(question_title)
    answer_tokens = tokenize(question_answer)  # 全量答案文本

    # 文件端 tokens
    file_text = f"{file_description} {file_path} {kb_description}"
    file_tokens = tokenize(file_text)

    # 分类关键词
    cat_keywords = set(kw.lower() for kw in KEYWORD_MAP.get(question_category, []))

    # 标题命中 (30% weight)
    title_hits = len(title_tokens & file_tokens)
    title_score = title_hits / max(len(title_tokens), 1) if title_tokens else 0

    # 答案命中 (30% weight) — 用全量答案
    answer_hits = len(answer_tokens & file_tokens)
    answer_score = answer_hits / max(len(answer_tokens), 1) if answer_tokens else 0

    # 文件描述命中 (30% weight) — 文件 tokens 在 标题+答案 中的覆盖率
    all_q_tokens = title_tokens | answer_tokens
    file_hits_in_q = len(file_tokens & all_q_tokens)
    file_score = file_hits_in_q / max(len(file_tokens), 1) if file_tokens else 0

    # 分类权重 (10%) — 文件描述中包含分类关键词的比例
    cat_hits = len(cat_keywords & file_tokens)
    cat_score = cat_hits / max(len(cat_keywords), 1)

    return title_score * 0.30 + answer_score * 0.30 + file_score * 0.30 + cat_score * 0.10


def import_references_keyword(dry_run=False, clear_first=False, top_k=5):
    """按关键词匹配关联知识库引用"""
    if clear_first:
        clear_references()

    conn = get_connection()
    questions = conn.execute(
        "SELECT id, title, answer, category FROM questions ORDER BY id"
    ).fetchall()
    print(f"  Questions in DB: {len(questions)}")

    total_created = 0
    matched_questions = 0
    score_distribution: List[int] = []

    for q in questions:
        qid = q["id"]
        category = q["category"]
        title = q["title"]
        answer = q["answer"]

        # 对每个知识库中同分类的文件计算匹配分
        candidates = []
        for kb_key, kb in KNOWLEDGE_BASES.items():
            if category not in kb["categories"]:
                continue
            files = kb["files"].get(category, [])
            for file_path, line_range, desc in files:
                score = compute_match_score(
                    title, answer, category,
                    desc, file_path, kb["repo_description"],
                )
                candidates.append((score, kb, file_path, line_range, desc))

        # Take Top-K, but if ALL scores are < 0.05, do a cross-category fallback
        if not candidates or max(c[0] for c in candidates) < 0.05:
            # Cross-category fallback: try matching against ALL knowledge base files
            for kb_key, kb in KNOWLEDGE_BASES.items():
                for cat, files in kb["files"].items():
                    for file_path, line_range, desc in files:
                        score = compute_match_score(
                            title, answer, cat if cat == category else "通用",
                            desc, file_path, kb["repo_description"],
                        )
                        candidates.append((score, kb, file_path, line_range, desc))

        # 取 Top-K
        candidates.sort(key=lambda x: x[0], reverse=True)
        top = candidates[:top_k]

        if not top:
            continue

        q_added = 0
        for score, kb, file_path, line_range, desc in top:
            if score < 0.05:  # 阈值太低的不关联
                continue
            if dry_run:
                print(f"  [DRY-RUN] Q{qid} [{category}] score={score:.3f} → {kb['repo_name']}: {desc[:60]}")
            else:
                try:
                    insert_reference({
                        "question_id": qid,
                        "repo_name": kb["repo_name"],
                        "repo_url": kb["repo_url"],
                        "file_path": file_path,
                        "line_range": line_range,
                        "code_snippet": "",
                        "description": desc,
                        "score": score,
                    })
                except Exception as e:
                    print(f"  WARN: insert failed Q{qid}: {e}")
                    continue
            q_added += 1

        if q_added > 0:
            matched_questions += 1
            total_created += q_added
            score_distribution.append(q_added)

    conn.close()

    if dry_run:
        print(f"\n[DRY-RUN] Will create {total_created} refs for {matched_questions}/{len(questions)} questions")
        print(f"  Avg refs per question: {total_created/matched_questions:.1f}" if matched_questions else "")
    else:
        print(f"\n[DONE] Created {total_created} refs for {matched_questions}/{len(questions)} questions")

    # Show distribution
    if matched_questions:
        dist = Counter(score_distribution)
        print(f"  Ref distribution: {dict(sorted(dist.items()))}")

    return total_created


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--clear", action="store_true", help="清空旧引用再导入")
    parser.add_argument("--top-k", type=int, default=5, help="每题最多关联 K 个引用（默认 5）")
    args = parser.parse_args()
    import_references_keyword(dry_run=args.dry_run, clear_first=args.clear, top_k=args.top_k)


if __name__ == "__main__":
    main()
