"""
LangGraph 模拟面试官工作流

State → Nodes → Edges 路由规则

关键设计：
- Graph 建模单轮面试循环：question → evaluate → critique
- "等待用户输入"在 API 层处理，不作为 Graph 节点
- 追问场景：critique 路由回 evaluate（用户再答→再评）
- 题目数据全部来自 SQLite，不再依赖内存中的 QUESTION_BANK
- 评估支持 LLM-as-Judge（需 LLM_ENABLED=true），失败时自动回退到启发式
"""

import json
import logging
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

from app.core import database as db
from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# 1. State 定义
# ============================================================

class InterviewState(TypedDict):
    """面试工作流的全局状态"""
    session_id: str
    difficulty: str

    current_question: dict | None  # 当前题目（来自 SQLite 的 dict）
    question_number: int
    total_questions: int

    messages: list[dict]
    current_answer: str

    evaluation: dict | None
    critique: str | None

    next_action: Literal["question", "evaluate", "critique", "end"]


# ============================================================
# 2. Node 节点定义
# ============================================================

def _evaluate_answer_heuristic(question: dict, user_answer: str) -> dict:
    """基于关键词匹配 + 答案长度做基础评估（LLM 不可用时的 fallback）"""
    expected_kw = question.get("expected_keywords", [])
    if isinstance(expected_kw, str):
        expected_kw = json.loads(expected_kw)

    keyword_hits = [kw for kw in expected_kw if kw.lower() in user_answer.lower()]
    hit_count = len(keyword_hits)
    total_kw = len(expected_kw)
    missing = [kw for kw in expected_kw if kw not in keyword_hits]

    coverage = hit_count / total_kw if total_kw > 0 else 0
    length_factor = min(len(user_answer) / 200, 1.0)

    score = round((coverage * 0.7 + length_factor * 0.3) * 100)

    return {
        "score": score,
        "keywords_matched": keyword_hits,
        "missing_keywords": missing,
        "coverage": round(coverage, 2),
    }


async def _evaluate_answer(question: dict, user_answer: str) -> dict:
    """评估候选人回答。优先用 LLM，失败时回退到启发式"""
    if settings.llm_enabled:
        try:
            from app.core.llm_client import get_llm_service
            svc = get_llm_service()
            result = await svc.evaluate_answer(question, user_answer)
            if result is not None:
                logger.info(f"[evaluate] LLM score={result.get('score')}")
                return result
            logger.warning("[evaluate] LLM returned None, falling back to heuristic")
        except Exception as e:
            logger.warning(f"[evaluate] LLM error: {e}, falling back to heuristic")

    return _evaluate_answer_heuristic(question, user_answer)


def question_node(state: InterviewState) -> dict:
    """Question_Node：根据用户选择的难度从 SQLite 题库抛题"""
    difficulty = state["difficulty"]
    q_number = state.get("question_number", 0) + 1

    # 从 SQLite 筛选对应难度的题目
    pool, _ = db.list_questions(difficulty=difficulty, page=1, page_size=1000)
    if not pool:
        pool, _ = db.list_questions(page=1, page_size=1000)

    idx = (q_number - 1) % len(pool)
    selected = pool[idx]

    return {
        "current_question": selected,
        "question_number": q_number,
        "messages": state.get("messages", []) + [{
            "role": "interviewer",
            "content": f"【第{q_number}题】(难度: {difficulty}) {selected['title']}"
        }],
        "evaluation": None,
        "critique": None,
        "next_action": "evaluate",
    }


async def evaluate_node(state: InterviewState) -> dict:
    """Evaluate_Node：接收用户回答，调用评估逻辑比对"""
    q_data = state.get("current_question")
    user_answer = state.get("current_answer", "")

    if not q_data:
        return {"next_action": "end"}

    evaluation = await _evaluate_answer(q_data, user_answer)

    return {
        "evaluation": evaluation,
        "next_action": "critique",
    }


def critique_node(state: InterviewState) -> dict:
    """
    Critique_Node（反思/评价节点）：
    - 回答太浅 (score < 50) → 追问 (route back to evaluate)
    - 回答合格且还有题 → 进入下一题 (route to question)
    - 回答合格且全做完 → 结束 (route to END)
    """
    evaluation = state.get("evaluation", {})
    score = evaluation.get("score", 0)
    question = state.get("current_question", {})

    score_ok = score >= 50
    all_questions_done = state.get("question_number", 0) >= state.get("total_questions", 3)

    if score_ok and not all_questions_done:
        critique_msg = (
            f"✅ 回答不错！得分 {score}/100。"
            f"你命中了关键词: {evaluation.get('keywords_matched', [])}。"
        )
        if evaluation.get("missing_keywords"):
            critique_msg += f"\n📖 补充知识点: {evaluation['missing_keywords']}。"
        critique_msg += "\n⏭️ 我们来看下一题…"
        return {
            "critique": critique_msg,
            "next_action": "question",
        }

    elif score_ok and all_questions_done:
        return {
            "critique": f"🎉 面试结束！本场表现优异：最终得分 {score}/100。你的 Agent 知识储备扎实，继续保持！",
            "next_action": "end",
        }

    else:  # score < 50 — 追问
        what_missing = evaluation.get("missing_keywords", [])
        critique_msg = (
            f"🤔 你的回答还不够深入。得分 {score}/100。"
            f"请补充以下知识点：{what_missing}。"
        )
        hint = question.get("hint", "")
        if hint:
            critique_msg += f"\n💡 提示：{hint}"

        return {
            "critique": critique_msg,
            "messages": state.get("messages", []) + [{
                "role": "interviewer",
                "content": critique_msg
            }],
            "next_action": "evaluate",
        }


# ============================================================
# 3. 条件路由函数
# ============================================================

def route_after_critique(state: InterviewState) -> str:
    """反思后路由：下一题 / 追问重评 / 结束"""
    action = state.get("next_action", "end")
    if action == "question":
        return "question"
    elif action == "evaluate":
        return "evaluate"
    else:
        return "end"


# ============================================================
# 4. 构建 StateGraph
# ============================================================

def build_interview_graph() -> StateGraph:
    """构建 LangGraph 面试工作流"""
    builder = StateGraph(InterviewState)

    builder.add_node("question", question_node)
    builder.add_node("evaluate", evaluate_node)
    builder.add_node("critique", critique_node)

    builder.set_entry_point("question")
    builder.add_edge("question", "evaluate")
    builder.add_edge("evaluate", "critique")

    builder.add_conditional_edges(
        "critique",
        route_after_critique,
        {"question": "question", "evaluate": "evaluate", "end": END},
    )

    return builder.compile()
