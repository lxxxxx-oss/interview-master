"""
LLM 客户端抽象层 — 供应商无关的 OpenAI 兼容接口

两层设计：
  LlmClient     — 低层 HTTP 传输（封装 AsyncOpenAI）
  LlmService    — 领域服务（评估、分类、元数据生成）

使用方式：
    from app.core.llm_client import get_llm_service
    svc = get_llm_service()
    result = await svc.evaluate_answer(question, user_answer)
    if result is None:  # LLM 不可用，回退到启发式
        result = _evaluate_answer_heuristic(...)
"""

import json
import logging
from typing import Optional, AsyncIterator

from openai import AsyncOpenAI, APIStatusError, APITimeoutError, RateLimitError
from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# LlmClient — HTTP 传输层
# ============================================================

class LlmClient:
    """封装 AsyncOpenAI，支持任意 OpenAI 兼容供应商"""

    def __init__(self):
        if not settings.llm_api_key:
            self._client = None
            logger.warning("LLM_API_KEY not set; all LLM calls will fall back to heuristic")
            return

        self._client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout=30.0,
            max_retries=2,
        )
        logger.info(
            f"[LlmClient] initialized: model={settings.llm_model}, "
            f"base_url={settings.llm_base_url}"
        )

    @property
    def is_available(self) -> bool:
        return self._client is not None and settings.llm_enabled

    async def chat_completion(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Optional[str]:
        """非流式对话补全，失败返回 None"""
        if not self.is_available:
            return None

        try:
            resp = await self._client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                temperature=temperature or settings.llm_temperature,
                max_tokens=max_tokens or settings.llm_max_tokens,
            )
            return resp.choices[0].message.content

        except (APITimeoutError, RateLimitError, APIStatusError) as e:
            logger.warning(f"LLM API error: {type(e).__name__}: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM unexpected error: {e}")
            return None

    async def chat_with_json_output(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
    ) -> Optional[dict]:
        """对话 + 强制 JSON 输出，自动解析，失败返回 None"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        text = await self.chat_completion(messages, temperature=temperature)
        if text is None:
            return None

        return _parse_json(text)

    async def chat_completion_stream(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """流式对话补全，逐 token yield。失败时 yield 空"""
        if not self.is_available:
            return

        try:
            stream = await self._client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                temperature=temperature or settings.llm_temperature,
                max_tokens=max_tokens or settings.llm_max_tokens,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
        except Exception as e:
            logger.warning(f"LLM stream error: {e}")
            return


# ============================================================
# LlmService — 领域服务层
# ============================================================

class LlmService:
    """在 LlmClient 之上提供面试领域的 LLM 能力"""

    def __init__(self, client: LlmClient | None = None):
        self._client = client or LlmClient()

    @property
    def is_available(self) -> bool:
        return self._client.is_available

    # ─── 面试评估 ─────────────────────────────────

    EVAL_SYSTEM_PROMPT = """\
你是一位资深的 AI Agent 领域面试官。你需要评估候选人对面试题的回答质量。

评分标准（0-100 分）：
- 80-100：全面覆盖核心知识点，有深度理解，能结合实践
- 60-79：覆盖主要知识点，理解正确但深度不足
- 40-59：涉及部分知识点，但理解不够透彻或有遗漏
- 0-39：回答过于简略，未命中核心知识点

请严格返回 JSON 格式（不要额外文字）：
{
  "score": 整数(0-100),
  "keywords_matched": ["命中的关键词"],
  "missing_keywords": ["遗漏的关键词"],
  "coverage": 浮点数(0.0-1.0, 表示语义覆盖度),
  "reasoning": "简短评估理由（中文，1-2句）"
}"""

    async def evaluate_answer(self, question: dict, user_answer: str) -> Optional[dict]:
        """
        LLM-as-Judge 评估回答质量。
        返回: {score, keywords_matched, missing_keywords, coverage, reasoning} | None
        """
        expected_kw = question.get("expected_keywords", [])
        if isinstance(expected_kw, str):
            try:
                expected_kw = json.loads(expected_kw)
            except json.JSONDecodeError:
                expected_kw = []

        user_prompt = f"""\
题目：{question['title']}
难度：{question.get('difficulty', 'medium')}
分类：{question.get('category', 'Agent基础')}
期望关键词：{json.dumps(expected_kw, ensure_ascii=False)}

候选人回答：
{user_answer}

请评估以上回答。"""

        return await self._client.chat_with_json_output(
            system_prompt=self.EVAL_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

    # ─── 题目分类 ─────────────────────────────────

    CLASSIFY_SYSTEM_PROMPT = """\
你是一位 AI Agent 领域专家。请对给定的面试题进行分类。

难度标准：
- easy：基础概念题，简单定义或列举
- medium：需要理解原理和流程
- hard：涉及架构设计、优化、对比、深入原理

分类选项（只能选一个）：
RAG、MCP协议、Function Calling、Prompt Engineering、记忆机制、模型架构、Agent基础、向量检索

严格返回 JSON：
{
  "difficulty": "easy"|"medium"|"hard",
  "category": "RAG"|"MCP协议"|"Function Calling"|"Prompt Engineering"|"记忆机制"|"模型架构"|"Agent基础"|"向量检索",
  "hint": "解题提示（中文，1-2句话）",
  "keywords": ["关键词1", "关键词2", ...]
}"""

    async def classify_question(self, title: str) -> Optional[dict]:
        """单题分类，返回 {difficulty, category, hint, keywords} | None"""
        return await self._client.chat_with_json_output(
            system_prompt=self.CLASSIFY_SYSTEM_PROMPT,
            user_prompt=f"题目：{title}",
        )

    async def batch_classify_questions(self, titles: list[str]) -> list[Optional[dict]]:
        """批量分类（一次 LLM 调用处理多题），返回与输入等长的结果列表"""
        if not self.is_available or not titles:
            return [None] * len(titles)

        numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))
        prompt = f"""请对以下 {len(titles)} 道面试题逐一分类。返回一个 JSON 数组，每个元素对应一道题：

{numbered}

返回格式（JSON 数组）：
[
  {{"index": 1, "difficulty": "...", "category": "...", "hint": "...", "keywords": [...]}},
  ...
]"""

        text = await self._client.chat_completion(
            messages=[
                {"role": "system", "content": self.CLASSIFY_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        if text is None:
            return [None] * len(titles)

        parsed = _parse_json(text)
        if isinstance(parsed, list):
            # 按 index 对齐
            results = []
            by_index = {item.get("index", 0): item for item in parsed if isinstance(item, dict)}
            for i in range(len(titles)):
                results.append(by_index.get(i + 1))
            return results
        return [None] * len(titles)

    # ─── 流式 Critique ─────────────────────────────

    async def stream_critique(
        self,
        question: dict,
        evaluation: dict,
        user_answer: str,
    ) -> AsyncIterator[str]:
        """流式生成面试官的评价反馈文本"""
        prompt = f"""\
题目：{question['title']}
候选人回答：{user_answer}
评分：{evaluation.get('score', 0)}/100
命中关键词：{evaluation.get('keywords_matched', [])}
遗漏关键词：{evaluation.get('missing_keywords', [])}

请用中文给出简短评价（2-4句话）：
- 得分<50：指出不足，给出改进建议和提示
- 得分≥50：肯定优点，简要补充可提升的方向
- 不要复述完整评分，直接给出自然的口语化反馈"""

        messages = [
            {"role": "system", "content": "你是一位亲切而严格的 AI Agent 面试官，用口语化的中文给候选人反馈。"},
            {"role": "user", "content": prompt},
        ]

        async for token in self._client.chat_completion_stream(
            messages=messages,
            temperature=0.7,
            max_tokens=300,
        ):
            yield token


# ============================================================
# 工具函数
# ============================================================

def _parse_json(text: str) -> Optional[dict | list]:
    """从 LLM 响应中解析 JSON，处理常见格式问题"""
    if not text:
        return None
    text = text.strip()
    # 去掉 markdown 代码块包裹
    if text.startswith("```"):
        lines = text.split("\n")
        # 移除首行 ```json 和末行 ```
        text = "\n".join(lines[1:]) if len(lines) > 1 else text
        if text.endswith("```"):
            text = text[:-3].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试提取第一个 { 或 [ 到最后一个 } 或 ]
        try:
            start = min(
                text.index("{") if "{" in text else len(text),
                text.index("[") if "[" in text else len(text),
            )
            end = max(
                text.rindex("}") if "}" in text else -1,
                text.rindex("]") if "]" in text else -1,
            )
            if start < end:
                return json.loads(text[start:end + 1])
        except (ValueError, json.JSONDecodeError):
            pass
        logger.warning(f"Failed to parse JSON from LLM response: {text[:200]}")
        return None


# ============================================================
# 全局单例
# ============================================================

_llm_service: LlmService | None = None


def get_llm_service() -> LlmService:
    """获取全局 LlmService 实例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LlmService()
    return _llm_service
