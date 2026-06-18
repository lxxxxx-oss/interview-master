#!/usr/bin/env python
"""
知识库引用导入脚本 — 将 5 个 GitHub 仓库按分类关联到题库

所有文件路径均已通过 GitHub API 实际验证（HTTP 200）。
用法：
    python -m app.scripts.import_references
    python -m app.scripts.import_references --dry-run
    python -m app.scripts.import_references --clear  # 先清空再导入
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.core.database import get_connection, insert_reference


# ─── 知识库仓库定义（路径已通过 GitHub API 验证）────────────────

KNOWLEDGE_BASES = {
    "hello-agents": {
        "repo_name": "datawhalechina/hello-agents",
        "repo_url": "https://github.com/datawhalechina/hello-agents",
        "repo_description": "从零开始构建智能体 — ReAct/Plan-and-Solve/Reflection 三种经典范式的完整讲解与 Python 实现",
        "categories": ["Agent基础", "记忆机制", "模型架构", "Prompt Engineering"],
        "files": {
            "Agent基础": [
                ("README.md", "L1", "全书总览：AI Agent 技术全景 — 从 LLM 到 Agent 的完整技术栈"),
                ("docs/chapter1/Chapter1-Introduction-to-Agents.md", "L1", "第一章：初识智能体 — Agent 核心概念、智能体定义与分类"),
                ("docs/chapter2/Chapter2-History-of-Agents.md", "L1", "第二章：智能体发展史 — 从规则系统到 LLM Agent 的演进路线"),
                ("docs/chapter4/Chapter4-Building-Classic-Agent-Paradigms.md", "L1", "第四章：经典范式构建 — ReAct、Plan-and-Solve、Reflection 原理与 Python 全实现"),
            ],
            "模型架构": [
                ("docs/chapter3/Chapter3-Fundamentals-of-Large-Language-Models.md", "L1", "第三章：大语言模型基础 — Transformer 架构、推理能力与 Agent 的模型底座"),
            ],
            "Prompt Engineering": [
                ("docs/chapter5/Chapter5-Building-Agents-with-Low-Code-Platforms.md", "L1", "第五章：低代码平台搭建 — Dify/Coze 等平台的 Agent 编排实践"),
            ],
            "记忆机制": [
                ("docs/chapter4/Chapter4-Building-Classic-Agent-Paradigms.md", "L30", "第四章相关节：Reflection 范式中的自我反思与记忆更新机制"),
            ],
        },
    },
    "all-in-rag": {
        "repo_name": "datawhalechina/all-in-rag",
        "repo_url": "https://github.com/datawhalechina/all-in-rag",
        "repo_description": "RAG 技术全栈指南 — 从数据准备到检索优化的完整 RAG 系统构建",
        "categories": ["RAG", "向量检索"],
        "files": {
            "RAG": [
                ("README.md", "L1", "RAG 全栈指南总览 — 四步构建完整 RAG 系统"),
                ("docs/chapter1/01_RAG_intro.md", "L1", "第一章：RAG 基础概念与架构设计 — 检索增强生成的核心理念"),
                ("docs/chapter1/02_preparation.md", "L1", "第一章：开发环境准备 — Python 环境配置与依赖安装"),
                ("docs/chapter1/03_get_start_rag.md", "L1", "第一章：快速上手 RAG — 最小化 RAG 系统搭建实战"),
                ("docs/chapter2/04_data_load.md", "L1", "第二章：数据加载 — 多格式文档解析与预处理"),
                ("docs/chapter2/05_text_chunking.md", "L1", "第二章：文本切片策略 — 固定大小/语义/递归等多种切分方式对比"),
            ],
            "向量检索": [
                ("docs/chapter3/06_vector_embedding.md", "L1", "第三章：向量嵌入 — Embedding 模型选型与文本向量化"),
                ("docs/chapter3/07_multimodal_embedding.md", "L1", "第三章：多模态嵌入 — 图像/文本联合向量化技术"),
                ("docs/chapter3/08_vector_db.md", "L1", "第三章：向量数据库 — Milvus/FAISS/Chroma 等主流方案对比"),
                ("docs/chapter3/09_milvus.md", "L1", "第三章：Milvus 实战 — 分布式向量数据库的安装与使用"),
                ("docs/chapter3/10_index_optimization.md", "L1", "第三章：索引优化 — ANN 近似搜索与检索性能调优"),
            ],
        },
    },
    "easy-vibe": {
        "repo_name": "datawhalechina/easy-vibe",
        "repo_url": "https://github.com/datawhalechina/easy-vibe",
        "repo_description": "Vibe Coding 2026 教程 — 初学者到精通的分步课程，涵盖现代 AI 编程范式与 Agent 开发",
        "categories": ["Agent基础", "Prompt Engineering"],
        "files": {
            "Agent基础": [
                ("README.md", "L1", "课程总览：AI 辅助编程的完整学习路径 — 从环境搭建到 Agent 开发"),
                ("CLAUDE.md", "L1", "项目配置文件：Agent 协作规则定义 — 展示 AI Agent 编程的工程实践"),
                ("docs/zh-cn/guide/introduction.md", "L1", "导论：Vibe Coding 核心理念 — AI 驱动的现代软件开发方法论"),
            ],
            "Prompt Engineering": [
                ("AGENTS.md", "L1", "Agent 指令设计：Prompt Engineering 在 Agent 协作中的实际应用范例"),
            ],
        },
    },
    "learn-claude-code": {
        "repo_name": "shareAI-lab/learn-claude-code",
        "repo_url": "https://github.com/shareAI-lab/learn-claude-code",
        "repo_description": "从零实现 Agent Harness — Bash 驱动的 nano claude-code 类 Agent 系统",
        "categories": ["Agent基础", "MCP协议", "Function Calling", "记忆机制"],
        "files": {
            "Agent基础": [
                ("README.md", "L1", "项目总览：从零构建 Agent Harness 的完整学习路线"),
                ("s01_agent_loop/README.md", "L1", "第一章：Agent Loop — 推理-行动-观察的完整循环机制"),
                ("s18_worktree_isolation/README.md", "L1", "第十八章：Worktree 隔离 — Agent 工作空间隔离与并发安全"),
                ("docs/zh/s01-the-agent-loop.md", "L1", "中文文档：Agent 循环详解 — 从消息输入到工具调用的全流程"),
            ],
            "MCP协议": [
                ("s19_mcp_plugin/README.md", "L1", "第十九章：MCP Plugin — 外部能力路由，动态发现并调用 MCP Server 工具"),
            ],
            "Function Calling": [
                ("s02_tool_use/README.md", "L1", "第二章：Tool Use — 工具调用的分发机制、参数解析与并发执行策略"),
                ("docs/zh/s02-tool-use.md", "L1", "中文文档：Tool Use 详解 — Function Calling 在 Agent 中的实现模式"),
            ],
            "记忆机制": [
                ("s09_memory/README.md", "L1", "第九章：Memory — Agent 记忆系统设计，短期/长期记忆的存储与检索"),
            ],
        },
    },
    "agentic-design-patterns": {
        "repo_name": "xindoo/agentic-design-patterns",
        "repo_url": "https://github.com/xindoo/agentic-design-patterns",
        "repo_description": "Google Agent 设计模式 — 中文翻译版全书，含 21 章 Agent 设计模式深度解析",
        "categories": ["Agent基础", "Prompt Engineering", "MCP协议", "RAG", "记忆机制", "Function Calling", "模型架构"],
        "files": {
            "Agent基础": [
                ("README.md", "L1", "全书总览：21 种 Agentic Design Patterns 的完整目录与阅读指南"),
                ("chapters/Chapter 1_ Prompt Chaining.md", "L1", "第一章：Prompt Chaining — 将复杂任务分解为链式提示步骤"),
                ("chapters/Chapter 2_ Routing.md", "L1", "第二章：Routing — 根据输入动态选择处理路径的分发模式"),
                ("chapters/Chapter 3_ Parallelization.md", "L1", "第三章：Parallelization — 并行执行多个子任务以提升吞吐量"),
                ("chapters/Chapter 7_ Multi-Agent Collaboration.md", "L1", "第七章：Multi-Agent 协作 — 多 Agent 分工与消息传递架构"),
            ],
            "Prompt Engineering": [
                ("chapters/Chapter 1_ Prompt Chaining.md", "L1", "第一章：Prompt Chaining 提示链 — 逐步引导 LLM 完成复杂推理"),
            ],
            "Function Calling": [
                ("chapters/Chapter 5_ Tool Use.md", "L1", "第五章：Tool Use — Agent 调用外部工具/API 的设计模式"),
            ],
            "模型架构": [
                ("chapters/Chapter 4_ Reflection.md", "L1", "第四章：Reflection — 自我反思与迭代优化的 Agent 推理架构"),
                ("chapters/Chapter 6_ Planning.md", "L1", "第六章：Planning — 提前规划执行路径的智能体设计"),
                ("chapters/Chapter 17_ Reasoning Techniques.md", "L1", "第十七章：推理技术 — CoT/ToT/ReAct 等深度推理模式对比"),
            ],
            "记忆机制": [
                ("chapters/Chapter 8_ Memory Management.md", "L1", "第八章：Memory Management — Agent 的上下文记忆与会话持久化策略"),
                ("chapters/Chapter 9_ Learning and Adaptation.md", "L1", "第九章：Learning and Adaptation — Agent 从反馈中持续学习的机制"),
            ],
            "MCP协议": [
                ("chapters/Chapter 10_ Model Context Protocol (MCP).md", "L1", "第十章：MCP 协议详解 — 模型上下文协议的标准接口与实现"),
            ],
            "RAG": [
                ("chapters/Chapter 14_ Knowledge Retrieval (RAG).md", "L1", "第十四章：RAG 知识检索 — 检索增强生成在 Agent 中的应用模式"),
            ],
        },
    },
}


def clear_references():
    """清空 code_references 表"""
    conn = get_connection()
    conn.execute("DELETE FROM code_references")
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM code_references").fetchone()[0]
    conn.close()
    print(f"  Cleared code_references table, now {count} rows")


def import_references(dry_run=False, clear_first=False):
    """按分类将知识库引用关联到所有题目"""
    if clear_first:
        clear_references()

    conn = get_connection()

    # 获取所有题目及其分类
    questions = conn.execute("SELECT id, title, category FROM questions ORDER BY id").fetchall()
    print(f"  Questions in DB: {len(questions)}")

    total_created = 0
    matched = 0

    for q in questions:
        qid = q["id"]
        category = q["category"]
        q_added = 0

        for kb_key, kb in KNOWLEDGE_BASES.items():
            if category in kb["categories"]:
                files = kb["files"].get(category, [])
                for file_path, line_range, desc in files:
                    if dry_run:
                        print(f"  [DRY-RUN] Q{qid} [{category}] → {kb['repo_name']}: {file_path}")
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
                            })
                        except Exception as e:
                            print(f"  WARN: insert failed Q{qid} / {kb['repo_name']}: {e}")
                            continue
                    q_added += 1

        if q_added > 0:
            matched += 1
            total_created += q_added

        if not dry_run and matched >= 10 and matched % 40 == 0:
            print(f"  Progress: {matched}/{len(questions)} questions, {total_created} refs")

    conn.close()

    if dry_run:
        print(f"\n[DRY-RUN] Will create {total_created} refs for {matched} questions")
    else:
        print(f"\n[DONE] Created {total_created} refs for {matched}/{len(questions)} questions")
    return total_created


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="不实际写入，只预览")
    parser.add_argument("--clear", action="store_true", help="先清空 code_references 表再导入")
    args = parser.parse_args()

    import_references(dry_run=args.dry_run, clear_first=args.clear)


if __name__ == "__main__":
    main()
