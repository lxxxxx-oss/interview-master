# API 接口文档

> 最后更新：2026-06-19

## 后端地址

- 开发环境：`http://localhost:8000`
- 生产环境：通过 Nginx 反向代理，`/api/*` → FastAPI

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| SQLITE_PATH | `backend/data/questions.db` | SQLite 数据库文件路径 |
| HOST | `0.0.0.0` | 服务监听地址 |
| PORT | `8000` | 服务端口 |
| CORS_ORIGINS | `http://localhost:5173,...` | CORS 允许的域名（逗号分隔） |
| CRAWL_DELAY | `2.0` | 牛客网爬取请求间隔（秒） |
| CRAWL_MAX_PAGES | `5` | 每次爬取最大页数 |
| NOWCODER_COOKIE | 无 | 牛客网登录 Cookie（可选） |
| DEBUG | `false` | 调试模式 |
| SERVE_STATIC | `false` | 是否托管前端静态文件（无 Nginx 时用） |

---

## 面试会话

### POST /api/interview/start

初始化面试会话，返回第一道题。

```
POST /api/interview/start
Content-Type: application/json

{"difficulty": "medium", "total_questions": 3}

→ 200 {
    "session_id": "40dfd439",
    "question": {
      "id": 2, "title": "...", "difficulty": "easy", "category": "RAG",
      "hint": "...", "expected_keywords": ["RAG", "检索", ...]
    },
    "question_number": 1,
    "total_questions": 3
  }
```

### POST /api/interview/answer

提交回答，SSE 流式返回评估 + 批判反馈。

```
POST /api/interview/answer
Content-Type: application/json

{"session_id": "40dfd439", "answer": "RAG 是检索增强生成..."}

→ SSE: event:evaluate → event:critique → event:question(如有下一题)
```

**SSE 事件格式：**

```
event: evaluate
data: {"step":"evaluate","evaluation":{"score":66,"keywords_matched":["RAG",...],"missing_keywords":["切片"],"coverage":0.8}}

event: critique
data: {"step":"critique","critique":"✅ 回答不错！得分 66/100...","next_action":"question"}

event: question
data: {"step":"question","question":{...},"question_number":2,"total_questions":3}
```

### GET /api/interview/sessions

列出活跃会话（调试用）。

---

## 题库（SQLite 数据源）

### GET /api/questions

分页查询题库。

| 查询参数 | 说明 |
|----------|------|
| difficulty | `easy` / `medium` / `hard` |
| company | 公司名 |
| category | 标签名 |
| search | 搜索关键词（FTS5 全文搜索 + BM25 相关性排序） |
| search_type | `fts`（默认，FTS5 全文搜索）/ `like`（LIKE 子串匹配回退） |
| page | 页码（默认 1） |
| page_size | 每页条数（默认 12） |

```
GET /api/questions?difficulty=hard&page=1&page_size=5

→ 200 {
    "questions": [{id, title, difficulty, company, category, ...}, ...],
    "total": 7, "page": 1, "page_size": 5
  }
```

### GET /api/questions/{id}

题目详情（含关联的代码引用，按 score 降序排列）。

**返回体新增字段（2026-06-19）：**

```json
→ 200 {
    "id": 4,
    "title": "...",
    "answer": "...",
    "references": [
      {
        "id": 123, "question_id": 4,
        "repo_name": "datawhalechina/hello-agents",
        "repo_url": "https://github.com/datawhalechina/hello-agents",
        "file_path": "docs/chapter4/...", "line_range": "L1",
        "description": "...",
        "score": 0.624
      }, ...
    ],
    "referenceAnchors": [
      {
        "refId": 123, "score": 0.624,
        "snippet": "答案中的匹配片段…",
        "position": 128
      }, ...
    ]
  }
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `references` | array | 知识库引用列表，按 `score` 降序 |
| `references[].score` | float (0-1) | 关键词匹配综合评分（详见下文） |
| `referenceAnchors` | array | 答案内联锚点，引用在答案中的位置映射 |
| `referenceAnchors[].refId` | int | 对应 `references` 中的引用 ID |
| `referenceAnchors[].snippet` | string | 答案中匹配位置的上下文片段 |
| `referenceAnchors[].position` | int | 匹配点在答案中的字符偏移 |

**相关性计算算法：**

```
score = title_hit_rate × 0.30 + answer_hit_rate × 0.30 + file_hit_rate × 0.30 + category_hit_rate × 0.10
```

| 分项 | 权重 | 计算方式 |
|------|------|----------|
| 标题命中率 | 30% | 题目关键词在文件描述/路径中的命中比例 |
| 答案命中率 | 30% | 答案关键词在文件描述/路径中的命中比例 |
| 文件覆盖度 | 30% | 文件关键词在题目（标题+答案）中的覆盖比例 |
| 分类匹配度 | 10% | 文件描述中包含题目分类关键词的比例 |

**关键词提取：** 从预定义的 `KEYWORD_MAP` 中按题目分类取出关键词集合（每类 15-20 个技术术语），分别在题目文本和文件描述中匹配命中。

**引用筛选：**
- Top-K = 8，每题最多 8 条引用
- 最低阈值 0.05，低于该分数的引用不关联
- 同分类不足时触发跨分类回退匹配

**前端展现规则：**

| 指标 | 规则 |
|------|------|
| 排序 | 按 score 降序，后端 `ORDER BY score DESC` |
| 折叠 | 默认展示 Top 3，其余通过「展开全部 N 条引用」展开 |
| 相关度标签 | score > 0.28 → 高相关 🟢；0.12–0.28 → 中相关 🟠；其余 → 低相关 |
| 答案锚点 | `referenceAnchors` 生成 `[1]` `[2]` 编号标记，点击滚动到对应卡片 |
| 卡片高亮 | 点击锚点后 2 秒蓝色高亮动画 |

### GET /api/filters

获取可选筛选值（难度/公司/标签的所有去重值）。

### GET /api/stats

题库统计（总数、按难度分布、按来源分布、最近爬取记录）。

---

## 管理

### POST /api/admin/crawl

触发牛客网爬取。

```
POST /api/admin/crawl
Content-Type: application/json

{"max_pages": 5}

→ 200 {"status": "success", "pages_crawled": 5, "new_items": 12}
```

### PUT /api/admin/questions/{id}

更新题目字段。需要 `X-Admin-Token` 请求头验证管理员身份。

```
PUT /api/admin/questions/1
Content-Type: application/json
X-Admin-Token: <admin-token>

{
  "title": "...",
  "difficulty": "hard",
  "company": "ByteDance",
  "category": "Agent基础",
  "hint": "...",
  "answer": "..."
}

→ 200 {完整题目对象（含引用）}
→ 401 Missing X-Admin-Token header
→ 403 Invalid admin token
→ 404 Question not found
```

所有字段均为可选，仅更新提供的字段。`expected_keywords` 也可更新。

### DELETE /api/admin/questions/{id}

删除题目及关联的 `code_references`（级联删除）。需要 `X-Admin-Token` 请求头。

```
DELETE /api/admin/questions/1
X-Admin-Token: <admin-token>

→ 200 {"status": "deleted", "id": 1}
→ 401 Missing X-Admin-Token header
→ 403 Invalid admin token
→ 404 Question not found
```

**权限配置**：通过环境变量 `ADMIN_TOKEN` 设置管理员 token（默认值 `agent-interview-admin-2026`）。后续将升级为 JWT/OAuth2 方案。

---

## LangGraph 工作流节点

| 节点 | 函数 | 说明 |
|------|------|------|
| question_node | `app.core.interview_workflow.question_node` | 从 SQLite 题库出题 |
| evaluate_node | `app.core.interview_workflow.evaluate_node` | 关键词匹配评分 |
| critique_node | `app.core.interview_workflow.critique_node` | 追问/通过/结束 路由 |
| build_interview_graph | `app.core.interview_workflow.build_interview_graph()` | 构建编译后的 StateGraph |

**路由规则：**

```
critique → question (score≥50 且有下一题)
critique → evaluate (score<50 追问)
critique → END      (score≥50 且全部完成)
```
