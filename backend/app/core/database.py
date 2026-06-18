"""
SQLite 数据访问层

表结构：
  questions       — 面试题目
  code_references  — 关联的知识库文档引用
  crawl_log        — 爬取日志
"""

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.core.config import settings


# ============================================================
# 数据库连接管理
# ============================================================

def get_connection() -> sqlite3.Connection:
    """获取数据库连接（自动创建 data 目录和表）"""
    db_path = Path(settings.sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # 更好的并发读
    conn.execute("PRAGMA foreign_keys=ON")
    _ensure_tables(conn)
    return conn


def _ensure_tables(conn: sqlite3.Connection):
    """建表（幂等，首次调用自动创建）"""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            difficulty TEXT NOT NULL CHECK(difficulty IN ('easy', 'medium', 'hard')),
            company TEXT,
            category TEXT NOT NULL,
            hint TEXT NOT NULL DEFAULT '',
            answer TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'nowcoder' CHECK(source IN ('local', 'nowcoder')),
            source_url TEXT,
            expected_keywords TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(title, source_url)
        );

        CREATE TABLE IF NOT EXISTS code_references (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            repo_name TEXT NOT NULL,
            repo_url TEXT NOT NULL,
            file_path TEXT NOT NULL,
            line_range TEXT NOT NULL DEFAULT 'L1',
            code_snippet TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS crawl_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL DEFAULT 'nowcoder',
            pages_crawled INTEGER NOT NULL DEFAULT 0,
            new_items INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'success',
            error_message TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);
        CREATE INDEX IF NOT EXISTS idx_questions_company ON questions(company);
        CREATE INDEX IF NOT EXISTS idx_questions_category ON questions(category);
        CREATE INDEX IF NOT EXISTS idx_questions_source ON questions(source);
        CREATE INDEX IF NOT EXISTS idx_code_refs_question ON code_references(question_id);
    """)


# ============================================================
# 题目 CRUD
# ============================================================

def list_questions(
    difficulty: Optional[str] = None,
    company: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    source: Optional[str] = None,
    page: int = 1,
    page_size: int = 12,
) -> tuple[list[dict], int]:
    """分页查询题目列表"""
    conn = get_connection()
    conditions = []
    params: list = []

    if difficulty:
        conditions.append("difficulty = ?")
        params.append(difficulty)
    if company:
        conditions.append("company = ?")
        params.append(company)
    if category:
        conditions.append("category = ?")
        params.append(category)
    if source:
        conditions.append("source = ?")
        params.append(source)
    if search:
        conditions.append("(title LIKE ? OR answer LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    # 总数
    count_sql = f"SELECT COUNT(*) FROM questions {where}"
    total = conn.execute(count_sql, params).fetchone()[0]

    # 分页数据 — 有搜索词时按相关性排序（标题命中 > 答案命中），否则按 id 倒序
    offset = (page - 1) * page_size
    if search:
        order = "ORDER BY (CASE WHEN title LIKE ? THEN 2 WHEN answer LIKE ? THEN 1 ELSE 0 END) DESC, id DESC"
        order_params = [f"%{search}%", f"%{search}%"]
    else:
        order = "ORDER BY id DESC"
        order_params = []
    data_sql = f"SELECT * FROM questions {where} {order} LIMIT ? OFFSET ?"
    rows = conn.execute(data_sql, params + order_params + [page_size, offset]).fetchall()

    conn.close()
    return [_row_to_dict(r) for r in rows], total


def get_question(qid: int) -> Optional[dict]:
    """获取单题详情（含代码引用）"""
    conn = get_connection()
    q_row = conn.execute("SELECT * FROM questions WHERE id = ?", (qid,)).fetchone()
    if not q_row:
        conn.close()
        return None

    refs = conn.execute(
        "SELECT * FROM code_references WHERE question_id = ?", (qid,)
    ).fetchall()

    result = _row_to_dict(q_row)
    result["references"] = [_row_to_dict(r) for r in refs]
    conn.close()
    return result


def get_questions_by_difficulty(difficulty: Optional[str] = None) -> list[dict]:
    """按难度获取题目列表"""
    questions, _ = list_questions(difficulty=difficulty, page=1, page_size=1000)
    return questions


def insert_question(data: dict) -> int:
    """
    插入题目（source_url 去重）
    返回新 id，如果已存在返回 None
    """
    conn = get_connection()
    source_url = data.get("source_url")

    if source_url:
        existing = conn.execute(
            "SELECT id FROM questions WHERE title = ? AND source_url = ?",
            (data["title"], source_url),
        ).fetchone()
        if existing:
            conn.close()
            return None  # 去重

    cursor = conn.execute(
        """
        INSERT INTO questions (title, difficulty, company, category, hint, answer,
                               source, source_url, expected_keywords)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["title"],
            data.get("difficulty", "medium"),
            data.get("company"),
            data.get("category", "通用"),
            data.get("hint") or generate_tailored_hint(
                data["title"],
                data.get("category", "通用"),
                data.get("difficulty", "medium"),
            ),
            data.get("answer", ""),
            data.get("source", "nowcoder"),
            source_url,
            json.dumps(data.get("expected_keywords", []), ensure_ascii=False),
        ),
    )
    conn.commit()
    qid = cursor.lastrowid
    conn.close()
    return qid


def update_question(qid: int, data: dict) -> bool:
    """
    Update question fields. Only fields present in data are updated.
    Returns True on success, False if question not found.
    """
    allowed = {
        "title", "difficulty", "company", "category",
        "hint", "answer", "source", "source_url", "expected_keywords",
    }
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return False

    if "expected_keywords" in updates and not isinstance(updates["expected_keywords"], str):
        updates["expected_keywords"] = json.dumps(updates["expected_keywords"], ensure_ascii=False)

    updates["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [qid]

    conn = get_connection()
    cursor = conn.execute(f"UPDATE questions SET {set_clause} WHERE id = ?", values)
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected


def delete_question(qid: int) -> bool:
    """
    Delete a question and its associated code references (CASCADE).
    Returns True on success, False if question not found.
    """
    conn = get_connection()
    cursor = conn.execute("DELETE FROM questions WHERE id = ?", (qid,))
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected


def get_filter_options() -> dict:
    """获取筛选选项（去重后的难度/公司/标签列表）"""
    conn = get_connection()
    difficulties = [r[0] for r in conn.execute(
        "SELECT DISTINCT difficulty FROM questions ORDER BY difficulty"
    ).fetchall()]
    companies = [r[0] for r in conn.execute(
        "SELECT DISTINCT company FROM questions WHERE company IS NOT NULL ORDER BY company"
    ).fetchall()]
    categories = [r[0] for r in conn.execute(
        "SELECT DISTINCT category FROM questions ORDER BY category"
    ).fetchall()]
    conn.close()
    return {
        "difficulties": difficulties,
        "companies": companies,
        "categories": categories,
    }


def get_stats() -> dict:
    """题库统计"""
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    by_difficulty = {
        row[0]: row[1]
        for row in conn.execute(
            "SELECT difficulty, COUNT(*) FROM questions GROUP BY difficulty"
        ).fetchall()
    }
    by_source = {
        row[0]: row[1]
        for row in conn.execute(
            "SELECT source, COUNT(*) FROM questions GROUP BY source"
        ).fetchall()
    }
    last_crawl = conn.execute(
        "SELECT * FROM crawl_log ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    return {
        "total": total,
        "by_difficulty": by_difficulty,
        "by_source": by_source,
        "last_crawl": _row_to_dict(last_crawl) if last_crawl else None,
    }


# ============================================================
# 代码引用 CRUD
# ============================================================

def insert_reference(data: dict):
    """插入代码引用"""
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO code_references (question_id, repo_name, repo_url, file_path,
                                      line_range, code_snippet, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["question_id"],
            data["repo_name"],
            data["repo_url"],
            data["file_path"],
            data.get("line_range", "L1"),
            data.get("code_snippet", ""),
            data.get("description", ""),
        ),
    )
    conn.commit()
    conn.close()


# ============================================================
# 爬取日志
# ============================================================

def log_crawl(source: str, pages: int, new_items: int, status: str = "success",
               error: Optional[str] = None):
    """记录爬取日志"""
    conn = get_connection()
    conn.execute(
        "INSERT INTO crawl_log (source, pages_crawled, new_items, status, error_message) "
        "VALUES (?, ?, ?, ?, ?)",
        (source, pages, new_items, status, error),
    )
    conn.commit()
    conn.close()


# ============================================================
# 工具函数
# ============================================================

# ============================================================
# 工具函数
# ============================================================

def generate_tailored_hint(title: str, category: str, difficulty: str = "medium") -> str:
    """为题目生成有针对性的启发提示，引导答题思路。"""
    t = title.lower()

    # ============ RAG ============
    if category == "RAG":
        if "流程" in t:
            return "提示：先画出 RAG 的完整链路（索引→检索→增强→生成），再逐一说明每个环节的输入输出。建议结合一个具体场景（如客服问答）来串联。"
        if "挑战" in t or "局限" in t or "缺陷" in t:
            return "提示：从检索质量、上下文窗口、幻觉风险、响应延迟四个维度分析。每个挑战举一个实际场景中的反例，然后给出当前的缓解方案。"
        if "评估" in t or "指标" in t:
            return "提示：分三层思考——检索层（Recall/Precision/MRR）、生成层（Faithfulness/Relevance）、端到端层（用户满意度/任务完成率）。说明每层为什么需要不同的评估指标。"
        if "优化" in t or "改进" in t:
            return "提示：对照标准 RAG 的瓶颈点来组织回答：切片策略→检索方式→重排序→Prompt 构造。每个环节给一个可落地的优化方案，不仅说\"怎么做\"还要说\"为什么有效\"。"
        if "embedding" in t:
            return "提示：先解释 Embedding 在 RAG 中承担两个角色——文档索引时的向量化和查询时的语义映射。然后对比稠密向量和稀疏向量的取舍场景，说明为什么生产环境常用混合方案。"
        if "chunk" in t or "切片" in t:
            return "提示：从三个约束条件出发——模型上下文长度上限、检索的语义完整性、计算成本。举例说明固定长度切分和语义切分的实际效果差异。"
        if "rerank" in t or "重排序" in t:
            return "提示：先区分初检（粗排，用 Bi-Encoder 快速召回）和重排序（精排，用 Cross-Encoder 精确打分）的定位差异。解释为什么 Cross-Encoder 更准但更慢，以及如何在实际系统中权衡。"
        if "召回" in t or "检索" in t:
            return "提示：从倒排索引→向量检索→混合检索→重排序递进说明。每一层解释它解决什么问题，查准率和查全率在每一层如何变化。"
        if "向量" in t or "vector" in t:
            return "提示：先解释为什么需要将文本转为向量（语义相似度计算），再对比常见向量数据库（Milvus/FAISS/Pinecone）的技术选型要点——索引算法、分布式、过滤支持。"
        return "提示：从 RAG 的核心目的出发——\"让 LLM 在回答前先查阅外部知识\"。分别说明检索阶段和生成阶段的关键设计，最好举一个你实际使用过的场景。"

    # ============ MCP协议 ============
    if category == "MCP协议":
        if "server" in t or "服务端" in t:
            return "提示：从三个核心接口切入——列出工具（tools/list）、调用工具（tools/call）、列出资源（resources/list）。重点说明工具定义的 JSON Schema 格式要求，给一个简单的 Python MCP Server 代码示例。"
        if "client" in t or "客户端" in t:
            return "提示：从客户端的三项职责展开——连接管理（stdio/HTTP/SSE 三种传输适配）、工具注册与路由、结果回传与错误处理。可以画一个客户端连接多个 MCP Server 的拓扑图。"
        if "传输" in t or "stdio" in t or "sse" in t or "http" in t:
            return "提示：对比三种传输方式的适用场景——stdio（本地进程间通信，零配置但仅限本机）、HTTP（跨网络但需考虑鉴权）、SSE（适合服务端推送场景）。用决策表格总结。"
        if "安全" in t or "鉴权" in t or "auth" in t:
            return "提示：从三个层面分析——传输层（TLS/SSH 加密通道）、认证层（Bearer Token / OAuth2）、授权层（工具级别的细粒度权限控制）。说明为什么 MCP 协议本身不定义安全机制，而是由传输层和应用层负责。"
        if "a2a" in t:
            return "提示：先区分两个协议的定位——MCP 解决 Agent 与外部工具的通信，A2A 解决 Agent 与 Agent 的通信。从发现机制、任务描述格式、状态同步方式三方面对比。"
        if "工具" in t or "tool" in t:
            return "提示：从工具的全生命周期展开——定义（JSON Schema 设计是核心）→发现（tools/list）→调用（tools/call）→结果处理。强调 Schema 描述质量直接决定 LLM 选择工具的准确率，给一个好坏对比。"
        return "提示：一句话概括 MCP——让 AI 安全、标准化地访问外部工具的协议。然后从动机（为什么需要统一协议）、核心概念（Client/Server/Tool/Resource）、技术实现三层递进回答，搭配一个实际场景串联。"

    # ============ Function Calling ============
    if category == "Function Calling":
        if "react" in t or "ReAct" in t:
            return "提示：用类比说明——Function Calling 是\"手\"（执行动作），ReAct 是\"脑+手\"（推理+执行循环）。画一个 ReAct 循环图：Thought→Action→Observation→Thought...说明 Function Calling 在 Action 环节的具体角色。"
        if "schema" in t or "定义" in t or "描述" in t:
            return "提示：从 LLM 的视角思考——它需要知道函数名、用途描述、参数类型和必填项。Schema 写得好不好直接影响调用准确率，举一个模糊描述 vs 精确描述让模型选错/选对工具的对比。"
        if "并行" in t or "parallel" in t:
            return "提示：区分两种并行场景——无依赖并行（如同时查天气+查股价）和有依赖编排（先查城市代码再查天气）。说明如何通过依赖图（DAG）编排调用顺序，以及如何处理部分并行任务失败的情况。"
        if "错误" in t or "异常" in t or "error" in t:
            return "提示：分类讨论——工具返回业务错误（如参数不合法）、网络超时、LLM 幻觉调用不存在的工具。每种场景给出具体的重试策略或降级方案，最好有伪代码。"
        if "限" in t or "幻觉" in t:
            return "提示：从两个角度分析——①模型可能调用不存在的工具或编造参数（靠 Schema 约束+校验层兜底）；②模型可能忽略工具返回结果（在 System Prompt 中明确要求基于工具结果回答）。"
        return "提示：从\"让 LLM 学会使用工具\"这个核心需求出发。先解释 Function Calling 的基本流程（定义工具→模型输出函数名+参数→执行→返回结果给模型），再举例说明它在 Agent 中的定位——相当于 Agent 的\"手\"。"

    # ============ Prompt Engineering ============
    if category == "Prompt Engineering":
        if "注入" in t or "injection" in t or "安全" in t:
            return "提示：先分类攻击面——直接注入（用户输入覆盖系统指令）、间接注入（外部文档含恶意指令）、多模态注入（图片中嵌入指令）。每类给出具体防护手段：输入清洗、分隔符隔离、权限最小化。"
        if "context engineering" in t or "上下文工程" in t:
            return "提示：先一句话区分——Prompt Engineering 关注\"怎么说\"（单次指令的措辞），Context Engineering 关注\"给什么背景\"（构建完整的上下文环境）。然后从信息组织、知识注入时机、上下文窗口管理三个维度对比两者的差异。Context Engineering 是更高层的系统设计，决定了 Prompt 能发挥多大效果。"
        if "cot" in t or "思维链" in t:
            return "提示：先解释 CoT 的核心理念——让模型\"说出思考过程\"比直接要答案更可靠。然后对比 Zero-shot CoT（只需加\"Let's think step by step\"）和 Few-shot CoT（需要给范例推理过程）的效果差异和使用成本。"
        if "few" in t:
            return "提示：从\"给模型看几个例子学习模式\"出发。说明 Few-shot 的核心要素——示例质量比数量重要、示例顺序影响输出分布、标签均衡性能更好。给一个正例一个反例对比效果。"
        if "模板" in t or "template" in t:
            return "提示：好的 Prompt 模板 = 角色定义 + 任务描述 + 输出格式 + 约束条件 + 示例。从可维护性和可复用性两个角度分析——为什么硬编码 Prompt 是反模式，模板化能带来什么好处。"
        if "长度" in t or "上下文" in t or "context" in t:
            return "提示：解释\"Lost in the Middle\"现象——模型对上下文开头和结尾的信息利用最好，中间部分容易被忽略。给出三种应对策略：重要信息放首尾、分段压缩摘要、用 RAG 减少无关上下文。"
        return "提示：从 Prompt 的结构化设计入手——好的 Prompt 包含角色、任务、约束、输出格式四个要素。用一个实际任务演示从简单 Prompt 逐步优化的迭代过程，每一步说明改善了什么问题。"

    # ============ 记忆机制 ============
    if category == "记忆机制":
        if "短期" in t or "short" in t:
            return "提示：短期记忆 = 当前会话的上下文窗口。从两个技术维度展开——①滑动窗口 vs 摘要压缩的取舍；②何时需要\"忘记\"旧信息（达到 Token 上限或话题切换时）。给出一个对话系统中管理短期记忆的具体方案。"
        if "长期" in t or "long" in t:
            return "提示：长期记忆 = 跨会话持久化存储。核心挑战是\"存什么、怎么查、何时更新\"。对比三种方案——全文存储+关键词检索、向量数据库语义检索、知识图谱结构化存储，说明各自的查询精度和维护成本。"
        if "上下文" in t or "窗口" in t:
            return "提示：先解释上下文窗口的本质限制（Transformer 的 O(n²) 注意力复杂度）。然后介绍三种优化方向——滑动窗口注意力（如 Mistral）、Ring Attention（分布式长序列处理）、上下文压缩（LLMLingua 等）。结合实际 Agent 场景说明选型考虑。"
        return "提示：从人脑记忆的类比出发——感觉记忆（当前输入）→工作记忆（上下文窗口）→长期记忆（外部存储）。逐一说明在 Agent 中对应的技术实现，以及三者之间的信息流转机制。"

    # ============ 模型架构 ============
    if category == "模型架构":
        if "切换" in t or "兼容" in t or "适配" in t:
            return "提示：核心思路是定义统一的 LLM 抽象层（Adapter 模式）。从三个层面设计——①统一的 chat/completion 接口抽象；②模型特定的参数映射（不同模型的 temperature/top_p 默认值和取值范围不同）；③错误处理和重试策略的标准化。画一个多模型路由架构图会更清晰。"
        if "harness" in t or "驾驭" in t:
            return "提示：Harness 的三要素是状态管理、工具编排、错误恢复。从这三个维度展开——状态如何序列化和恢复、工具调用的依赖图和并行策略、异常时的回退和重试机制。可以类比操作系统的进程管理来理解。"
        if "structured output" in t or "结构化输出" in t:
            return "提示：从三个层次说明——①Prompt 约束（最弱，依赖模型遵循指令的意愿）；②JSON Mode（中等，保证 JSON 格式但不保证字段名和类型）；③Tool Calling / Structured Output API（最强，Schema 驱动，严格匹配字段）。每层给出适用场景和失败案例。"
        if "agentic" in t or "coding" in t:
            return "提示：从三个维度对比传统 Coding Assistant 和 Agentic Coding——①主动性（被动补全 vs 主动规划任务并拆解步骤）；②工具使用（仅写代码 vs 读写文件+执行命令+Git 操作）；③自主决策（按字面提示执行 vs 理解目标后自主选择方案）。"
        if "异构" in t or "tpu" in t or "芯片" in t:
            return "提示：异构计算的三个关键挑战——①算子兼容性（不同芯片支持的算子集合不同，需要统一中间表示）；②精度差异（TPU 偏好 bfloat16 而 GPU 常用 float16）；③调度策略（如何根据模型结构和负载选择最优芯片）。重点说明 XLA/MLIR 等中间表示层的价值。"
        return "提示：先明确是讨论训练阶段还是推理部署阶段。然后从模型选型→接口适配→部署上线→性能监控四个阶段展开，每个阶段说明关键考量和技术方案。"

    # ============ Agent基础 ============
    if category == "Agent基础":
        if "structured output" in t or "结构化输出" in t:
            return "提示：从三个层次说明——①Prompt 约束（最弱，依赖模型遵循指令的意愿）；②JSON Mode（中等，保证 JSON 格式但不保证字段名和类型）；③Tool Calling / Structured Output API（最强，Schema 驱动，严格匹配字段）。每层给出适用场景和失败案例，重点说明为什么第三层是 Agent 可靠性的基石。"
        if "规划" in t or "plan" in t:
            return "提示：对比两种规划范式——①ReAct（推理和行动交替进行，灵活应变但可能偏离目标）；②Plan-and-Execute（先规划全流程再执行，效率高但缺乏应变能力）。结合场景说明何时用哪种，以及如何结合两者实现分层规划。"
        if "工具" in t or "tool" in t:
            return "提示：从工具调用的全链路思考——发现（有哪些可用工具）→选择（该用哪个最合适）→调用（参数怎么填正确）→验证（返回结果对不对）→纠错（不对怎么办）。重点说明工具选择策略：语义匹配和规则路由的取舍。"
        if "编排" in t or "orchestrat" in t:
            return "提示：从单 Agent 到多 Agent 的递进展开。单 Agent：线性链/ReAct/DAG 工作流。多 Agent：顺序流水线、并行协作、层级委派。每类画一个简单的拓扑图并说明消息传递机制和适用场景。"
        if "评估" in t or "评测" in t or "eval" in t:
            return "提示：从三个维度建立评估体系——①任务完成率（端到端，最重要，看最终是否达成目标）；②中间步骤质量（工具选择准确率、推理路径合理性）；③鲁棒性（异常输入处理、工具失败恢复能力）。强调 Agent 评估比单模型评估更难，因为涉及多步交互和环境反馈。"
        if "loop" in t or "循环" in t:
            return "提示：Agent 循环的本质是\"感知→思考→行动→观察\"的持续迭代。用一个具体例子演示——用户说\"帮我订明天去北京的机票\"，Agent 需要经历多少轮循环、每轮做什么、可能在哪里出问题。这个例子能很好展示 Agent 循环的复杂性。"
        if "可靠" in t or "鲁棒" in t or "错误" in t or "恢复" in t:
            return "提示：从三个层次设计容错——①预防层（输入校验、工具 Schema 严格约束）；②检测层（输出格式检查、工具结果验证、置信度阈值）；③恢复层（自动重试、降级到备用工具、最终人工介入）。每层给出具体的实现方式。"
        if "状态" in t or "state" in t:
            return "提示：Agent 状态管理的核心问题——①状态粒度（对话级/任务级/步骤级各存什么）；②持久化策略（内存/sqlite/redis 的取舍）；③状态恢复（从中断处继续执行的能力）。比较 LangGraph Checkpoint 机制和自定义状态管理的优劣。"
        return "提示：围绕 Agent 的核心公式展开：Agent = LLM + 规划能力 + 工具使用 + 记忆系统。分析题目侧重哪个维度，先把该维度的基本原理讲清楚，再说明它和其他三个维度如何协同工作。"

    # ============ 向量检索 ============
    if category == "向量检索":
        if "bm25" in t or "混合" in t:
            return "提示：先解释两种检索的原理差异——BM25 基于词频统计擅长精确关键词匹配，向量检索基于语义相似度擅长模糊语义匹配。然后说明混合检索的融合策略：RRF（倒数排名融合，无需调参）和加权求和（需调权重但更灵活）各自的适用场景。"
        if "数据库" in t or "milvus" in t or "faiss" in t:
            return "提示：从选型的四个维度比较——①索引算法（HNSW 高召回/IVF 低内存/PQ 高压缩的取舍）；②分布式能力（单机轻量 vs 集群扩展）；③过滤支持（标量过滤+向量过滤能否组合）；④运维成本（Milvus 功能全但重，FAISS 轻量但缺持久化和分布式）。"
        return "提示：先一句话解释向量检索的本质——\"将文本语义相似度转化为向量空间中的距离计算\"。然后从索引构建、相似度度量（余弦/欧氏/内积的选择）、近似最近邻搜索（ANN，牺牲少量精度换速度）三个环节展开。"

    # ============ Fallback ============
    hints = {
        "RAG": "提示：从\"检索\"和\"生成\"两个核心环节分别展开思考。检索端关注如何找到最相关的文档（Embedding→Chunk→ReRank），生成端关注如何将检索结果有效融入 Prompt。最好举一个实际应用的例子。",
        "MCP协议": "提示：从\"让 AI 安全、标准化地使用外部工具\"这个核心目标出发。先讲协议的分层设计（传输层/消息层/能力层），再用一个具体的工具调用例子串联起完整流程。",
        "Function Calling": "提示：围绕\"LLM 如何精确地选择和执行工具\"这个核心问题。从工具定义（Schema 设计是关键）→工具选择（路由策略）→结果处理（格式化回传给模型）三个环节展开。",
        "Prompt Engineering": "提示：好 Prompt 的核心公式 = 角色设定 + 任务描述 + 约束条件 + 输出格式 + 示例。围绕这个公式组织回答，每个部分说明它解决什么问题，给一个正例和反例的对比。",
        "记忆机制": "提示：把人脑记忆模型（瞬时记忆→短期工作记忆→长期记忆）映射到 Agent 技术栈。重点说明三类记忆各自用什么技术实现、如何触发检索、以及遗忘/淘汰策略。",
        "模型架构": "提示：从\"模型是 Agent 的发动机，但好的架构应该能换发动机\"这个比喻出发。关注点不是某个模型本身有多强，而是如何设计适配层让 Agent 与底层模型解耦。",
        "向量检索": "提示：从\"计算机如何理解两个文本的语义相似度\"出发。先讲 Embedding 的直观含义（把文本映射到高维空间中的点），再讲 ANN 索引如何加速检索，最后说混合检索为什么是生产环境的标配。",
        "Agent基础": "提示：围绕 Agent 的核心公式展开：Agent = LLM + 规划能力 + 工具使用 + 记忆系统。先分析题目侧重哪个维度，把该维度的基本原理讲清楚，再说明它和其他三个维度如何协同工作形成一个完整的 Agent。",
    }
    return hints.get(category, "提示：先理解题目考察的核心概念，从定义、原理、实践三个层面递进回答。如果能在回答中结合一个实际项目经验或生产环境案例，会更有说服力。")


def _row_to_dict(row: sqlite3.Row) -> dict:
    """sqlite3.Row → 普通 dict，自动反序列化 JSON 字段"""
    d = dict(row)
    if "expected_keywords" in d and isinstance(d["expected_keywords"], str):
        try:
            d["expected_keywords"] = json.loads(d["expected_keywords"])
        except json.JSONDecodeError:
            d["expected_keywords"] = []
    return d
