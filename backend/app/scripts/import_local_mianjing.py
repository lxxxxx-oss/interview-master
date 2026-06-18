#!/usr/bin/env python
"""
一次性导入脚本：解析本地面经 Markdown 文件 → SQLite

用法：
    python -m app.scripts.import_local_mianjing

后续面经更新后重新运行此脚本即可增量导入（相同 source_url 去重）。
"""

import sys
import re
from pathlib import Path
from dataclasses import dataclass

# 确保 backend 目录在 Python path 中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.core.database import get_connection, insert_question
from app.core.config import settings


@dataclass
class ParsedQuestion:
    title: str = ""
    answer_lines: list[str] = None
    difficulty: str = "medium"
    company: str = ""
    category: str = "Agent基础"

    def __post_init__(self):
        if self.answer_lines is None:
            self.answer_lines = []


def categorize(title: str) -> str:
    """根据题目标题自动分类"""
    title_lower = title.lower()
    if any(kw in title_lower for kw in ["rag", "检索", "向量", "知识库", "bm25", "embedding", "嵌入"]):
        return "RAG"
    if any(kw in title_lower for kw in ["mcp", "协议", "server"]):
        return "MCP协议"
    if any(kw in title_lower for kw in ["function call", "工具调用", "tool"]):
        return "Function Calling"
    if any(kw in title_lower for kw in ["prompt", "提示"]):
        return "Prompt Engineering"
    if any(kw in title_lower for kw in ["记忆", "memory", "短期", "长期"]):
        return "记忆机制"
    if any(kw in title_lower for kw in ["模型", "model", "架构", "多模型"]):
        return "模型架构"
    if any(kw in title_lower for kw in ["规划", "plan", "react", "agent"]):
        return "Agent基础"
    return "Agent基础"


def guess_difficulty(title: str) -> str:
    """简单启发式：根据关键词猜测难度"""
    title_lower = title.lower()
    if any(kw in title_lower for kw in ["区别", "设计", "架构", "优化", "为什么引入"]):
        return "hard"
    if any(kw in title_lower for kw in ["流程", "实现", "设计", "如何做", "怎么做"]):
        return "medium"
    return "easy"


def generate_keywords(title: str, category: str) -> list[str]:
    """根据题目标题和分类自动生成评估关键词"""
    title_lower = title.lower()
    keywords = set()

    category_kw_map = {
        "RAG": ["RAG", "检索", "生成", "向量化", "Embedding", "切片", "重排序", "Rerank", "FAISS", "知识库"],
        "MCP协议": ["MCP", "JSON-RPC", "initialize", "tools/list", "tools/call", "stdio", "HTTP", "SSE"],
        "Function Calling": ["Function Calling", "Schema", "工具", "tool", "调用", "Tool Role"],
        "Prompt Engineering": ["Prompt", "CoT", "Few-shot", "Zero-shot", "推理", "ReAct"],
        "记忆机制": ["短期记忆", "长期记忆", "上下文窗口", "向量数据库", "嵌入", "Embedding", "检索", "持久化"],
        "模型架构": ["适配器", "Adapter", "多模型", "热更新", "统一接口", "stream", "chat"],
        "向量检索": ["BM25", "混合检索", "RRF", "向量检索", "Rerank", "Cross-Encoder", "语义"],
        "Agent基础": ["Agent", "ReAct", "规划", "推理", "执行", "工具", "编排", "DAG"],
    }

    cat_kw = category_kw_map.get(category, ["Agent"])
    for kw in cat_kw:
        if kw.lower() in title_lower:
            keywords.add(kw)

    # 如果标题匹配太少，补充分类默认关键词
    if len(keywords) < 3:
        for kw in cat_kw[:5]:
            keywords.add(kw)

    return list(keywords)


def generate_hint(title: str) -> str:
    """为没有提示的题目生成基础提示"""
    hints = {
        "RAG": "从检索和生成两个核心环节展开，解释切片、向量化和重排序的作用。",
        "MCP": "从能力协商、工具发现、工具调用三个步骤展开。",
        "Function Call": "考虑 LLM 如何输出函数名和参数，以及结果如何返回给模型。",
        "记忆": "区分会话内上下文窗口和跨会话持久化存储。",
        "模型": "从适配器模式、统一接口抽象、动态路由三个层次考虑。",
        "Agent": "从推理、决策、执行的循环角度分析。",
    }
    cat = categorize(title)
    for key, hint in hints.items():
        if key.lower() in cat.lower():
            return hint
    return "结合相关概念的定义、原理和实际应用场景来回答。"


def generate_answer_knowledge(title: str) -> str:
    """为没有详细答案的题目生成知识点提纲"""
    return f"## {title}\n\n（详细答案请参考知识库文档或牛客网原帖）\n\n**关键知识点**：请查阅相关官方文档和面经原文获取完整答案。"


def parse_mianjing_markdown(filepath: str) -> list[ParsedQuestion]:
    """
    解析面经 Markdown 文件。
    支持格式：
      - # 标题 → 公司名
      - 数字序号问题 → 题目
      - （后续）（追问）→ 子问题
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    questions = []
    current_company = ""
    lines = content.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检测公司标题
        if line.startswith("# ") and "面经" in line:
            # 提取公司名
            company_match = re.search(r"(字节|快手|携程|滴滴|蚂蚁|美团|腾讯|百度|阿里|shopee|Shopee)", line)
            if company_match:
                current_company = company_match.group(1)

        # 检测问题行（数字开头）
        question_match = re.match(r"^(\d+)\.(.+)", line)
        if question_match:
            title = question_match.group(2).strip()
            # 跳过太短的文本和纯数字问题
            if len(title) < 5:
                continue

            # 处理追问标识
            if title.startswith("（追问）") or title.startswith("(追问)"):
                title = title[4:].strip()

            # 清理 Markdown 格式
            title = re.sub(r"\*\*(.+?)\*\*", r"\1", title)

            q = ParsedQuestion(
                title=title,
                difficulty=guess_difficulty(title),
                company=current_company,
                category=categorize(title),
            )
            q.answer_lines = [generate_answer_knowledge(title)]
            questions.append(q)

    return questions


def _classify_questions_batch(questions: list["ParsedQuestion"]) -> list["ParsedQuestion"]:
    """
    批量 LLM 分类题目元数据。LLM 不可用时 fallback 到启发式。
    原地修改并返回题目列表。
    """
    from app.core.config import settings

    if not questions:
        return questions

    titles = [q.title for q in questions]
    llm_results = [None] * len(questions)

    if settings.llm_enabled:
        try:
            from app.core.llm_client import get_llm_service
            svc = get_llm_service()
            import asyncio
            llm_results = asyncio.run(svc.batch_classify_questions(titles))
        except Exception:
            pass  # fallback below

    for i, q in enumerate(questions):
        r = llm_results[i] if i < len(llm_results) else None
        if r and isinstance(r, dict):
            q.difficulty = r.get("difficulty", guess_difficulty(q.title))
            q.category = r.get("category", categorize(q.title))
        else:
            q.difficulty = guess_difficulty(q.title)
            q.category = categorize(q.title)
    return questions


def import_to_sqlite(questions: list[ParsedQuestion]) -> int:
    """将解析出的题目导入 SQLite，返回新增数量"""
    # 先做批量 LLM 分类
    questions = _classify_questions_batch(questions)

    imported = 0
    skipped = 0

    for q in questions:
        qid = insert_question({
            "title": q.title,
            "difficulty": q.difficulty,
            "company": q.company or None,
            "category": q.category,
            "hint": generate_hint(q.title),
            "answer": "\n\n".join(q.answer_lines) if q.answer_lines else "",
            "source": "local",
            "source_url": None,
            "expected_keywords": generate_keywords(q.title, q.category),
        })
        if qid:
            imported += 1
        else:
            skipped += 1

    print(f"[import_local_mianjing] 导入完成: 新增 {imported}, 跳过(重复) {skipped}")
    return imported


def main():
    filepath = settings.local_mianjing_path
    if not Path(filepath).exists():
        print(f"[import_local_mianjing] 文件不存在: {filepath}，跳过导入。")
        return

    print(f"[import_local_mianjing] 解析文件: {filepath}")
    questions = parse_mianjing_markdown(filepath)
    print(f"[import_local_mianjing] 解析到 {len(questions)} 道题目")

    imported = import_to_sqlite(questions)

    # 显示统计
    from app.core.database import get_stats
    stats = get_stats()
    print(f"[import_local_mianjing] 题库当前总计: {stats['total']} 题")


if __name__ == "__main__":
    main()
