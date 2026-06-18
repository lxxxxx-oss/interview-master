"""
FastAPI SSE 流式接口 — 模拟面试

POST  /api/interview/start       → 初始化面试会话，返回第一个问题
POST  /api/interview/answer      → 提交回答，SSE 流式返回评估 + 批判反馈
GET   /api/interview/sessions    → 列出活跃会话
GET   /api/questions             → 题库列表（从 SQLite 读取）
GET   /api/questions/{id}        → 题目详情（含代码引用）
GET   /api/filters               → 筛选选项
GET   /api/stats                 → 题库统计
POST  /api/admin/crawl           → 触发牛客网爬取
"""

import asyncio
import json
import uuid
from typing import AsyncIterator

from fastapi import FastAPI
from pydantic import BaseModel, field_validator
from sse_starlette.sse import EventSourceResponse

from app.core.interview_workflow import (
    InterviewState,
    question_node,
    evaluate_node,
    critique_node,
)
from app.core import database as db

app = FastAPI(title="面试通 API", version="0.1.0")

# 面试会话状态（临时，会话结束即丢弃）
sessions: dict[str, InterviewState] = {}


# ============================================================
# 请求/响应模型
# ============================================================

class StartInterviewRequest(BaseModel):
    difficulty: str = "medium"  # easy | medium | hard
    total_questions: int = 3


class StartInterviewResponse(BaseModel):
    session_id: str
    question: dict
    question_number: int
    total_questions: int


class SubmitAnswerRequest(BaseModel):
    session_id: str
    answer: str


class CrawlRequest(BaseModel):
    max_pages: int = 5


class UpdateQuestionRequest(BaseModel):
    title: str | None = None
    difficulty: str | None = None
    company: str | None = None
    category: str | None = None
    hint: str | None = None
    answer: str | None = None
    source: str | None = None
    source_url: str | None = None
    expected_keywords: list[str] | None = None


# ============================================================
# 辅助函数
# ============================================================

def _init_state(session_id: str, difficulty: str, total_questions: int) -> InterviewState:
    return InterviewState(
        session_id=session_id,
        difficulty=difficulty,
        current_question=None,
        question_number=0,
        total_questions=total_questions,
        messages=[],
        current_answer="",
        evaluation=None,
        critique=None,
        next_action="question",
    )


def state_to_event(step: str, state: InterviewState) -> dict:
    """将 State 切片转换为 SSE event payload"""
    event = {
        "step": step,
        "session_id": state["session_id"],
    }

    if step == "question":
        event["question"] = state.get("current_question")
        event["question_number"] = state.get("question_number")
        event["total_questions"] = state.get("total_questions")

    elif step == "evaluate":
        event["evaluation"] = state.get("evaluation")

    elif step == "critique":
        event["critique"] = state.get("critique")
        event["next_action"] = state.get("next_action")

    elif step == "end":
        event["message"] = state.get("critique")
        event["evaluation"] = state.get("evaluation")

    return event


async def stream_evaluate_and_critique(state: InterviewState) -> AsyncIterator[dict]:
    """用户提交回答后，执行 evaluate → critique 并流式输出"""
    # 1) 评估（单事件）
    e_result = await evaluate_node(state)
    state.update(e_result)
    yield {"event": "evaluate", "data": json.dumps(state_to_event("evaluate", state), ensure_ascii=False)}
    await asyncio.sleep(0.2)

    # 2) 批判反馈 — 尝试流式 token，失败则回退到单事件
    c_result = critique_node(state)
    state.update(c_result)

    critique_text = state.get("critique", "")
    question = state.get("current_question", {})
    evaluation = state.get("evaluation", {})
    answer = state.get("current_answer", "")

    from app.core.config import settings
    if settings.llm_enabled and critique_text:
        try:
            from app.core.llm_client import get_llm_service
            svc = get_llm_service()
            token_count = 0
            async for token in svc.stream_critique(question, evaluation, answer):
                yield {"event": "token", "data": json.dumps({
                    "step": "critique_stream",
                    "token": token,
                }, ensure_ascii=False)}
                token_count += 1
                # 每 5 个 token 让出一次事件循环（不给浏览器一口气灌太多）
                if token_count % 5 == 0:
                    await asyncio.sleep(0.01)
            yield {"event": "done", "data": json.dumps({"step": "critique_stream"}, ensure_ascii=False)}
            return  # 流式输出成功，不 fallback
        except Exception:
            pass  # fallback to single event below

    yield {"event": "critique", "data": json.dumps(state_to_event("critique", state), ensure_ascii=False)}


async def _single_event(event: str, msg: str):
    """生成单条错误事件"""
    yield {"event": event, "data": json.dumps({"message": msg}, ensure_ascii=False)}


# ============================================================
# 面试端点
# ============================================================

@app.post("/api/interview/start", response_model=StartInterviewResponse)
async def start_interview(req: StartInterviewRequest):
    """初始化面试：创建会话 + 抛出第一道题（从 SQLite 题库选）"""
    session_id = str(uuid.uuid4())[:8]

    state = _init_state(session_id, req.difficulty, req.total_questions)
    q_result = question_node(state)
    state.update(q_result)
    sessions[session_id] = state

    return StartInterviewResponse(
        session_id=session_id,
        question=state["current_question"],
        question_number=state["question_number"],
        total_questions=state["total_questions"],
    )


@app.post("/api/interview/answer")
async def submit_answer(req: SubmitAnswerRequest):
    """提交回答 → SSE 流式返回评估 + 批判反馈"""
    state = sessions.get(req.session_id)
    if not state:
        return EventSourceResponse(
            _single_event("error", "会话不存在或已过期，请重新开始面试")
        )

    state["current_answer"] = req.answer
    state["messages"] = state.get("messages", []) + [{
        "role": "candidate",
        "content": req.answer
    }]

    async def event_stream():
        async for event in stream_evaluate_and_critique(state):
            yield event

        if state.get("next_action") == "question":
            q_result = question_node(state)
            state.update(q_result)
            yield {"event": "question", "data": json.dumps(state_to_event("question", state), ensure_ascii=False)}

    return EventSourceResponse(event_stream())


@app.get("/api/interview/sessions")
async def list_sessions():
    """列出活跃会话"""
    return {
        "count": len(sessions),
        "sessions": [
            {
                "session_id": sid,
                "difficulty": s["difficulty"],
                "question_number": s["question_number"],
                "total_questions": s["total_questions"],
            }
            for sid, s in sessions.items()
        ],
    }


# ============================================================
# 题库端点（SQLite）
# ============================================================

@app.get("/api/questions")
async def list_questions(
    difficulty: str | None = None,
    company: str | None = None,
    category: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 12,
):
    """题库列表，支持筛选 + 分页"""
    questions, total = db.list_questions(
        difficulty=difficulty,
        company=company,
        category=category,
        search=search,
        page=page,
        page_size=page_size,
    )
    return {
        "questions": questions,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@app.get("/api/questions/{qid}")
async def get_question_detail(qid: int):
    """题目详情（含答案 + 关联代码引用）"""
    q = db.get_question(qid)
    if not q:
        return {"error": "题目未找到"}, 404
    return q


@app.get("/api/filters")
async def get_filters():
    """获取筛选选项"""
    return db.get_filter_options()


@app.get("/api/stats")
async def get_stats():
    """题库统计"""
    return db.get_stats()


# ============================================================
# 管理端点
# ============================================================

# ─── 权限中间件（预留）────────────────────
# 当前直接放行，后续接入 JWT/OAuth2 时在此处校验
# 设置 ADMIN_TOKEN 环境变量可开启 token 校验

from fastapi import Header, HTTPException

ADMIN_TOKEN = __import__('os').getenv("ADMIN_TOKEN", "")


@app.put("/api/admin/questions/{qid}")
async def update_question_endpoint(
    qid: int,
    body: UpdateQuestionRequest,
    x_admin_token: str | None = Header(default=None),
):
    """Update a question"""
    if ADMIN_TOKEN and x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    success = db.update_question(qid, data)
    if not success:
        raise HTTPException(status_code=404, detail="Question not found")
    return db.get_question(qid)


@app.delete("/api/admin/questions/{qid}")
async def delete_question_endpoint(
    qid: int,
    x_admin_token: str | None = Header(default=None),
):
    """Delete a question with its references"""
    if ADMIN_TOKEN and x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    success = db.delete_question(qid)
    if not success:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"status": "deleted", "id": qid}


@app.post("/api/admin/crawl")
async def trigger_crawl(req: CrawlRequest = CrawlRequest()):
    """触发牛客网爬取（异步执行）"""
    try:
        from app.scripts.crawl_nowcoder import run_crawl
        pages, new_items = run_crawl(max_pages=req.max_pages)
        return {"status": "success", "pages_crawled": pages, "new_items": new_items}
    except ImportError:
        return {"status": "error", "message": "爬虫模块未安装（需要 playwright + chromium）"}, 500
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500
