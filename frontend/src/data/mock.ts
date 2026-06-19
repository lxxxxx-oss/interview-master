// ============================================================
// 面试通 — Mock 数据（基于本地面经 + 知识库提炼）
// 代码引用的 filePath/lineRange 基于各仓库实际文件结构
// ============================================================

import type { Question, QuestionDetail, CodeReference, FilterOptions } from '../types'

// ─── 代码引用 ───────────────────────────────────────────
// 注意：filePath 均为各仓库 main 分支上真实存在的文件路径
// lineRange 指向对应概念所在的章节（非精确行号时 GitHub 会定位到文件顶部）
const refs: Record<number, CodeReference[]> = {
  // 题目 1: ReAct vs Plan-and-Solve → hello-agents ch4 + agentic-design-patterns
  1: [
    {
      id: 1, questionId: 1,
      repoName: 'datawhalechina/hello-agents',
      repoUrl: 'https://github.com/datawhalechina/hello-agents',
      filePath: 'docs/chapter4/README.md',
      lineRange: 'L1',
      codeSnippet: `# 第四章：智能体经典范式构建\n\n本章手把手带你实现三种经典 Agent 范式：\n1. **ReAct** — 思考-行动-观察循环\n2. **Plan-and-Solve** — 先规划后执行\n3. **Reflection** — 自我反思迭代优化\n\n每种范式都包含完整 Python 实现代码。`,
      description: '三种经典 Agent 范式的完整讲解与代码实现',
      score: 0.42,
    },
    {
      id: 2, questionId: 1,
      repoName: 'xindoo/agentic-design-patterns',
      repoUrl: 'https://github.com/xindoo/agentic-design-patterns',
      filePath: 'README.md',
      lineRange: 'L1',
      codeSnippet: `# Agentic Design Patterns\n\n谷歌 Agent 设计模式一书的中文翻译版，涵盖：\n- ReAct Pattern\n- Plan-and-Solve Pattern\n- Reflection Pattern\n- Multi-Agent Collaboration\n\n在线阅读：https://adp.xindoo.xyz/`,
      description: 'Google Agent 设计模式 — 中文翻译版全书',
      score: 0.36,
    },
  ],
  // 题目 3: RAG 概念与流程 → all-in-rag
  3: [
    {
      id: 3, questionId: 3,
      repoName: 'datawhalechina/all-in-rag',
      repoUrl: 'https://github.com/datawhalechina/all-in-rag',
      filePath: 'README.md',
      lineRange: 'L1',
      codeSnippet: `# All-in-RAG\n\nRAG 技术全栈指南，覆盖从基础到进阶的全部内容：\n\n## 四步构建 RAG 系统\n1. **数据准备** — 多格式文档加载 + 文本分块\n2. **索引构建** — 向量化 + 向量数据库存储\n3. **检索优化** — 混合检索、查询重写、Rerank\n4. **生成集成** — 检索结果注入 LLM 生成回答\n\n在线阅读：https://datawhalechina.github.io/all-in-rag/`,
      description: 'RAG 技术全栈指南 — 四步构建 RAG 系统的完整教程',
      score: 0.38,
    },
  ],
  // 题目 6: MCP 协议 → learn-claude-code s19
  6: [
    {
      id: 4, questionId: 6,
      repoName: 'shareAI-lab/learn-claude-code',
      repoUrl: 'https://github.com/shareAI-lab/learn-claude-code',
      filePath: 's19_mcp_plugin/README.md',
      lineRange: 'L1',
      codeSnippet: `# s19: MCP Plugin — 外部能力路由\n\nMCP (Model Context Protocol) 让 Agent 动态发现并调用外部工具。\n\n## 核心组件\n- **MCPClient** — 发现并调用外部 MCP Server 的工具\n- **connect_mcp()** — 按名称连接 MCP Server\n- **assemble_tool_pool()** — 动态合并内置 + MCP 工具\n\n外部工具命名规则：\`mcp__{server}__{tool}\`（避免冲突并标识来源）`,
      description: 'MCP 协议插件实现 — Agent 动态对接外部工具服务',
      score: 0.51,
    },
  ],
  // 题目 10: Function Calling / 工具层设计
  10: [
    {
      id: 5, questionId: 10,
      repoName: 'shareAI-lab/learn-claude-code',
      repoUrl: 'https://github.com/shareAI-lab/learn-claude-code',
      filePath: 's02_tool_use/README.md',
      lineRange: 'L1',
      codeSnippet: `# s02: Tool Use — 工具调用\n\n## 核心机制\n- **TOOL_HANDLERS** — 工具分发映射表\n- **dispatch map** — 根据 LLM 输出的工具名路由到对应处理器\n- **并发调用** — 无依赖工具并行执行\n\n\`\`\`python\nTOOL_HANDLERS = {\n    "bash": handle_bash,\n    "read": handle_read,\n    "write": handle_write,\n    "grep": handle_grep,\n}\n\`\`\``,
      description: '工具调用层的分发机制与并发策略',
      score: 0.29,
    },
  ],
}

// ─── 面试题数据（来自本地面经） ───────────────────────────
const questions: Question[] = [
  {
    id: 1,
    title: 'ReAct 与 Plan-and-Solve 的区别是什么？各自适用什么场景？',
    difficulty: 'medium',
    company: '字节跳动',
    category: 'Agent基础',
    hint: '从执行流程、LLM 调用次数、对意外情况的适应能力三个维度思考。',
    answer: `## 核心区别

### ReAct（Reasoning + Acting）
**交替推理与执行**，每一步都经历 "思考 → 行动 → 观察" 循环。

- **适用场景**：环境不确定性强、需要根据中间结果动态调整策略的任务
- **优点**：灵活适应意外情况，每一步基于最新观察做出决策
- **缺点**：LLM 调用次数多，延迟较高

### Plan-and-Solve
**先规划后执行**，首先生成完整计划，再逐步执行每一步。

- **适用场景**：任务结构清晰、步骤可预见的场景
- **优点**：减少 LLM 调用次数，执行效率高
- **缺点**：如果中途出现意外，缺乏应变能力

### 实际项目中的选择
对于工具调用不确定的场景（如网络搜索），ReAct 更合适；
对于流程固定的场景（如数据处理 pipeline），Plan-and-Solve 更高效。`,
    source: 'local',
    sourceUrl: null,
    createdAt: '2025-05-15',
  },
  {
    id: 2,
    title: '如何设计 Agent 的多模型支持架构？多租户环境下模型切换是否支持热更新？',
    difficulty: 'hard',
    company: '字节跳动',
    category: '模型架构',
    hint: '考虑适配器模式、模型注册中心、以及租户隔离的方案。',
    answer: `## 多模型支持架构设计

### 1. 适配器模式 (Adapter Pattern)
\`\`\`python
class BaseLLMAdapter(ABC):
    @abstractmethod
    async def chat(self, messages: list, **kwargs) -> str: ...
    @abstractmethod
    async def stream(self, messages: list, **kwargs) -> AsyncIterator[str]: ...

class OpenAIAdapter(BaseLLMAdapter): ...
class ClaudeAdapter(BaseLLMAdapter): ...
class LocalModelAdapter(BaseLLMAdapter): ...
\`\`\`

### 2. 模型注册中心
通过配置文件或数据库维护模型注册表，运行时按需加载对应适配器。

### 3. 多租户热更新
- 每个租户维护独立配置（模型选择 + API Key）
- 使用 Redis 缓存租户配置，配置变更后立即生效
- 模型切换时无需重启服务，只需更新租户配置并刷新缓存
- 切换相互独立：租户 A 切换模型不影响租户 B`,
    source: 'local',
    sourceUrl: null,
    createdAt: '2025-05-20',
  },
  {
    id: 3,
    title: 'RAG 的概念是什么？其具体实现流程是怎样的？',
    difficulty: 'easy',
    company: '通用',
    category: 'RAG',
    hint: '从"检索 + 生成"两个核心环节出发，解释为什么要做切片、向量化、重排序。',
    answer: `## RAG (Retrieval-Augmented Generation)

**检索增强生成**——在 LLM 生成答案之前，先从外部知识库检索相关信息，再将检索结果作为上下文注入 Prompt，从而让模型生成更准确、更新、更可靠的回答。

### 标准流程

1. **文档加载** – 从 PDF / Markdown / 网页 / 数据库加载文档
2. **文档切分 (Chunking)** – 按语义边界将长文档切为 256~1024 token 的片段
3. **向量化 (Embedding)** – 用 embedding 模型将文本片段转为稠密向量
4. **向量存储** – 存入向量数据库（FAISS / Milvus / Pinecone）
5. **用户查询向量化** – 同样的 embedding 模型将用户问题转为向量
6. **相似度检索** – 在向量空间做 ANN 搜索，返回 TopK 最相似片段
7. **重排序 (Rerank)** – 用 Cross-Encoder 精排候选片段
8. **Prompt 拼接 + 生成** – 检索到的片段 + 用户问题 → LLM 生成答案`,
    source: 'local',
    sourceUrl: null,
    createdAt: '2025-05-22',
  },
  {
    id: 4,
    title: '什么是 Function Call？它的实现流程是什么？',
    difficulty: 'easy',
    company: '通用',
    category: 'Function Calling',
    hint: '考虑如何让 LLM 输出结构化的函数调用，以及如何将函数执行结果返回给 LLM。',
    answer: `## Function Calling

**Function Calling** 是让 LLM 能够"调用"外部工具/API 的能力。模型不直接执行函数，而是输出结构化的函数调用请求（函数名 + 参数），由外部运行时实际执行。

### 核心流程

1. **定义工具 Schema** — 用 JSON Schema 描述每个函数的名称、描述、参数
2. **发送工具定义** — 将 Schema 随用户消息一同发送给 LLM
3. **LLM 决策调用** — LLM 判断是否需要调用工具，若需要则返回函数名 + 参数
4. **执行函数** — 运行时解析 LLM 输出，实际调用对应函数
5. **返回结果** — 将函数执行结果以 \`tool\` role 消息追加到对话历史
6. **LLM 生成最终回答** — 模型基于工具返回结果生成面向用户的自然语言回答`,
    source: 'local',
    sourceUrl: null,
    createdAt: '2025-05-25',
  },
  {
    id: 5,
    title: 'Agent 的记忆系统如何设计？短期记忆和长期记忆有什么区别？',
    difficulty: 'medium',
    company: '快手',
    category: '记忆机制',
    hint: '短期记忆关注会话上下文窗口，长期记忆关注跨会话的信息持久化与检索。',
    answer: `## Agent 记忆系统设计

### 短期记忆 (Short-term Memory)
- **本质**：当前会话的对话历史，存在于 LLM 上下文窗口中
- **实现**：消息列表 \`[user, assistant, tool, ...]\`
- **限制**：受限于模型上下文长度（8K / 32K / 128K / 200K tokens）
- **策略**：滑动窗口、摘要压缩、关键信息提取

### 长期记忆 (Long-term Memory)
- **本质**：跨会话持久化的结构化信息
- **实现**：向量数据库 + 结构化存储
- **内容**：用户偏好、历史决策、知识事实
- **策略**：
  - **写入**：从对话中提取关键信息 → 向量化 → 存入向量库
  - **读取**：当前查询向量化 → 相似度检索 → 注入上下文
  - **更新**：新信息覆盖或合并到已有记忆

### 关键区别

| 维度 | 短期记忆 | 长期记忆 |
|------|---------|---------|
| 生命周期 | 单次会话 | 跨会话持久 |
| 存储位置 | 上下文窗口 | 向量数据库 |
| 容量 | 受窗口限制 | 近乎无限 |
| 访问方式 | 直接拼接 | 相似度检索 |`,
    source: 'local',
    sourceUrl: null,
    createdAt: '2025-06-01',
  },
  {
    id: 6,
    title: 'MCP 协议的交互流程是怎样的？Agent 如何与 MCP Server 通信？',
    difficulty: 'medium',
    company: '滴滴',
    category: 'MCP协议',
    hint: 'MCP 基于 JSON-RPC，先理解能力协商 → 工具发现 → 工具调用的流程。',
    answer: `## MCP (Model Context Protocol) 交互流程

### 协议概述
MCP 是 Anthropic 提出的开放协议，基于 **JSON-RPC 2.0**，定义了 AI 模型与外部工具/数据源之间的标准接口。

### 交互序列

\`\`\`
Client (Host/Agent)              MCP Server
    |                                  |
    |--- initialize (capabilities) --->|
    |<--- server info + capabilities --|
    |                                  |
    |--- tools/list ------------------>|
    |<--- tool definitions (JSON) -----|
    |                                  |
    |--- tools/call (name + args) ---->|
    |<--- tool result -----------------|
    |                                  |
    |--- resources/read -------------->|
    |<--- resource content ------------|
\`\`\`

### 传输方式
- **stdio**：子进程标准输入输出（本地工具）
- **HTTP + SSE**：远程服务器通信

### Agent 连接 MCP Server

\`\`\`python
# 使用 mcp 客户端库
from mcp import ClientSession, StdioServerParameters

async with ClientSession(stdio_params) as session:
    # 1. 初始化连接
    await session.initialize()
    # 2. 获取可用工具列表
    tools = await session.list_tools()
    # 3. 调用工具
    result = await session.call_tool("search", {"query": "..."})
\`\`\``,
    source: 'local',
    sourceUrl: null,
    createdAt: '2025-06-05',
  },
  {
    id: 7,
    title: 'RAG 检索中为什么引入 BM25？BM25 和向量检索如何组合？',
    difficulty: 'hard',
    company: '快手',
    category: '向量检索',
    hint: 'BM25 擅长关键词精确匹配，向量检索擅长语义理解——两者如何互补？',
    answer: `## BM25 + 向量检索的混合策略

### 为什么引入 BM25？

单独的向量检索有盲区：
- **精确匹配弱**：对专业术语、缩写、ID 等精确匹配不如关键词检索
- **BM25 的优势**：基于词频/逆文档频率，擅长处理罕见词和精确匹配

两者互补：BM25 保精确，向量检索保语义。

### 混合检索架构

\`\`\`python
# 1. 并行检索
bm25_results = bm25_index.search(query, top_k=20)
vector_results = vector_db.search(embed(query), top_k=20)

# 2. 融合排序 (RRF - Reciprocal Rank Fusion)
def rrf(results_a, results_b, k=60):
    scores = {}
    for rank, doc in enumerate(results_a):
        scores[doc.id] = scores.get(doc.id, 0) + 1 / (k + rank + 1)
    for rank, doc in enumerate(results_b):
        scores[doc.id] = scores.get(doc.id, 0) + 1 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

# 3. Rerank
candidates = rrf(bm25_results, vector_results)[:10]
final = cross_encoder.rerank(query, candidates)[:5]
\`\`\`

### 常见组合比例
- BM25:Vector ≈ 0.3:0.7 或通过 RRF 自动融合
- 具体比例需在验证集上实验确定`,
    source: 'local',
    sourceUrl: null,
    createdAt: '2025-06-08',
  },
  {
    id: 8,
    title: 'Agent 的任务规划怎么做？规划是由模型完成还是通过规则实现？',
    difficulty: 'medium',
    company: '快手',
    category: 'Agent基础',
    hint: '考虑端到端模型规划 vs 规则引擎 vs 混合方案各自的优劣。',
    answer: `## Agent 任务规划方案

### 方案一：模型驱动规划（端到端）
LLM 根据用户意图自主分解子任务、决定执行顺序。

**优点**：灵活、覆盖未预见场景
**缺点**：不可控、幻觉导致错误规划、延迟高

### 方案二：规则/编排引擎
预定义任务模板 + DAG 编排（如 LangGraph）。

**优点**：可控、可预测、低延迟
**缺点**：覆盖场景有限，维护成本高

### 方案三：混合方案（推荐）
1. **意图识别**：LLM 识别用户意图 → 映射到预定义模板
2. **模板匹配**：命中则走规则引擎快速执行
3. **Fallback**：未命中则 LLM 动态规划 + 人工审核

### 多工具调用顺序决策
- 有依赖关系的工具：按 DAG 拓扑序执行
- 无依赖关系：并行调用以降低延迟
- 工具调用失败：重试 + 降级策略`,
    source: 'local',
    sourceUrl: null,
    createdAt: '2025-06-10',
  },
  {
    id: 9,
    title: '什么是 Prompt Engineering？有哪些常用技术？',
    difficulty: 'easy',
    company: '通用',
    category: 'Prompt Engineering',
    hint: '从 Zero-shot、Few-shot、Chain-of-Thought 等经典技术入手。',
    answer: `## Prompt Engineering 常用技术

### 1. Zero-shot Prompting
直接提问，不给示例。
> "将以下英文翻译成中文：The future belongs to agents."

### 2. Few-shot Prompting
给出 2-3 个示例，引导模型按格式输出。
> "输入：苹果 → 输出：水果
>  输入：汽车 → 输出：交通工具
>  输入：Python → 输出："

### 3. Chain-of-Thought (CoT)
引导模型逐步推理。
> "Q: 小明有 5 个苹果，吃了 2 个，又买了 3 个，现在有几个？"
> "A: 让我们一步步思考..."

### 4. Role Prompting
> "你是一位资深后端工程师，请 review 以下代码..."

### 5. Structured Output
要求以 JSON 格式输出，减少解析错误。

### 6. ReAct Prompting
交替输出 Thought → Action → Observation，配合工具调用。`,
    source: 'local',
    sourceUrl: null,
    createdAt: '2025-06-12',
  },
  {
    id: 10,
    title: 'Agent 的 Tools/Function Calling 层如何设计？多工具调用时如何决定顺序？',
    difficulty: 'medium',
    company: '蚂蚁',
    category: 'Function Calling',
    hint: '从工具注册、Schema 定义、调用链编排三个层次来思考。',
    answer: `## Agent 工具层设计

### 1. 工具注册与 Schema

\`\`\`python
class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get_schemas(self) -> list[dict]:
        """返回所有工具的 OpenAI Function Schema"""
        return [t.to_openai_schema() for t in self._tools.values()]

    async def execute(self, name: str, args: dict) -> str:
        tool = self._tools[name]
        return await tool.run(**args)
\`\`\`

### 2. 多工具调用顺序决策

- **依赖分析**：解析工具间的输入/输出依赖，构建 DAG
- **无依赖工具**：并行调用（asyncio.gather）
- **有依赖工具**：按拓扑序依次执行
- **失败处理**：重试 2 次 → 降级 → 通知用户

### 3. 工具调用状态机

\`\`\`
PLANNING → EXECUTING → OBSERVING → EVALUATING
                ↑                        |
                └─── (need more) ────────┘
                         |
                    (done) → FINALIZING
\`\`\``,
    source: 'local',
    sourceUrl: null,
    createdAt: '2025-06-15',
  },
]

// ─── 构建带引用的题目详情 ────────────────────────────
export const getQuestionDetail = (id: number): QuestionDetail => {
  const q = questions.find((q) => q.id === id)
  if (!q) throw new Error(`Question ${id} not found`)
  return { ...q, references: refs[id] || [] }
}

// ─── 题目列表 ────────────────────────────────────────
export const getQuestions = (): Question[] => questions

// ─── 筛选选项 ─────────────────────────────────────────
export const getFilterOptions = (): FilterOptions => ({
  difficulties: ['easy', 'medium', 'hard'],
  companies: ['通用', '字节跳动', '快手', '滴滴', '蚂蚁', '美团', '携程'],
  categories: [
    'Agent基础', 'RAG', 'MCP协议', 'Function Calling',
    'Prompt Engineering', '记忆机制', '向量检索', '模型架构',
  ],
})
