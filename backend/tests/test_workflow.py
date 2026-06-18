"""
LangGraph 面试工作流单元测试 — 基于 SQLite 数据库
"""

import sys
import pytest
sys.path.insert(0, ".")


def _ensure_test_data():
    """确保 SQLite 中有一条带 keywords 的测试题目"""
    from app.core.database import get_connection, insert_question
    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM questions WHERE title LIKE '%RAG%概念%' AND source='local'"
    ).fetchone()
    if not existing:
        insert_question({
            "title": "RAG 的概念是什么？具体实现流程包含哪些环节？",
            "difficulty": "easy",
            "company": "通用",
            "category": "RAG",
            "hint": "从检索和生成两个核心环节展开，解释切片、向量化和重排序的作用。",
            "answer": "RAG 是检索增强生成...",
            "source": "local",
            "source_url": None,
            "expected_keywords": ["RAG", "检索", "生成", "向量化", "Embedding", "切片", "重排序", "Rerank", "FAISS", "知识库"],
        })
    conn.close()


def _get_test_question() -> dict:
    """从 SQLite 获取一条有完整 keywords 的测试题目"""
    from app.core.database import get_connection
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM questions WHERE source='local' AND title LIKE '%RAG%概念%' LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row)


def test_question_node():
    """测试：question_node 应从 SQLite 正确抛出对应难度的题目"""
    from app.core.interview_workflow import question_node, InterviewState

    state = InterviewState(
        session_id="test",
        difficulty="easy",
        current_question=None,
        question_number=0,
        total_questions=3,
        messages=[],
        current_answer="",
        evaluation=None,
        critique=None,
        next_action="question",
    )

    result = question_node(state)
    assert result["question_number"] == 1
    assert result["current_question"]["difficulty"] == "easy"
    assert result["next_action"] == "evaluate"
    assert len(result["messages"]) == 1
    assert result["messages"][0]["role"] == "interviewer"


@pytest.mark.asyncio
async def test_evaluate_node_good_answer():
    """测试：好的回答应得高分"""
    _ensure_test_data()
    from app.core.interview_workflow import evaluate_node, InterviewState

    q = _get_test_question()

    state = InterviewState(
        session_id="test",
        difficulty="easy",
        current_question=q,
        question_number=1,
        total_questions=3,
        messages=[],
        current_answer="RAG 是检索增强生成。流程包括文档加载、切分、向量化、向量存储、相似度检索、重排序，最后通过 LLM 生成答案。关键组件有 Embedding、FAISS、Rerank。",
        evaluation=None,
        critique=None,
        next_action="evaluate",
    )

    result = await evaluate_node(state)
    assert result["evaluation"] is not None
    assert result["evaluation"]["score"] >= 50
    assert "RAG" in result["evaluation"]["keywords_matched"]
    assert result["next_action"] == "critique"


@pytest.mark.asyncio
async def test_evaluate_node_poor_answer():
    """测试：过于简短的回复应得低分"""
    _ensure_test_data()
    from app.core.interview_workflow import evaluate_node, InterviewState

    q = _get_test_question()

    state = InterviewState(
        session_id="test",
        difficulty="easy",
        current_question=q,
        question_number=1,
        total_questions=3,
        messages=[],
        current_answer="就是一种检索技术。",
        evaluation=None,
        critique=None,
        next_action="evaluate",
    )

    result = await evaluate_node(state)
    assert result["evaluation"]["score"] < 50


def test_critique_node_trigger_followup():
    """测试：低分时应触发追问"""
    _ensure_test_data()
    from app.core.interview_workflow import critique_node, InterviewState

    q = _get_test_question()

    state = InterviewState(
        session_id="test",
        difficulty="easy",
        current_question=q,
        question_number=1,
        total_questions=3,
        messages=[],
        current_answer="...",
        evaluation={"score": 20, "keywords_matched": [], "missing_keywords": ["RAG", "Embedding", "向量化"]},
        critique=None,
        next_action="critique",
    )

    result = critique_node(state)
    assert result["next_action"] == "evaluate"


def test_critique_node_pass_and_continue():
    """测试：高分且还有题，应进入下一题"""
    _ensure_test_data()
    from app.core.interview_workflow import critique_node, InterviewState

    q = _get_test_question()

    state = InterviewState(
        session_id="test",
        difficulty="easy",
        current_question=q,
        question_number=1,
        total_questions=3,
        messages=[],
        current_answer="...",
        evaluation={"score": 80, "keywords_matched": ["RAG", "向量化", "Embedding"], "missing_keywords": []},
        critique=None,
        next_action="critique",
    )

    result = critique_node(state)
    assert result["next_action"] == "question"


def test_critique_node_all_done():
    """测试：做完所有题高分结束"""
    _ensure_test_data()
    from app.core.interview_workflow import critique_node, InterviewState

    q = _get_test_question()

    state = InterviewState(
        session_id="test",
        difficulty="easy",
        current_question=q,
        question_number=3,
        total_questions=3,
        messages=[],
        current_answer="...",
        evaluation={"score": 85, "keywords_matched": ["RAG", "Embedding"], "missing_keywords": []},
        critique=None,
        next_action="critique",
    )

    result = critique_node(state)
    assert result["next_action"] == "end"


def test_build_graph():
    """测试：graph 编译成功，包含所有节点"""
    from app.core.interview_workflow import build_interview_graph

    graph = build_interview_graph()
    node_names = list(graph.nodes.keys())
    assert "question" in node_names
    assert "evaluate" in node_names
    assert "critique" in node_names
