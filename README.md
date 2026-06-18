# AI 面试通 (Interview Master)

面向 AI 方向的面试题库平台，已收录 **248 道**面试真题（14 家公司 + 通用知识）。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 18 + TypeScript + Ant Design + Zustand + Tailwind CSS |
| 后端 | Python + FastAPI + SSE 流式 API |
| AI 编排 | LangGraph（面试工作流） |
| 数据 | SQLite |

## 快速启动

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

环境变量（可选）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| SQLITE_PATH | backend/data/questions.db | 数据库路径 |
| LLM_ENABLED | false | 启用 LLM 评估 |
| LLM_API_KEY | - | LLM API Key |

### 前端

```bash
cd frontend
npm install
npx vite
```

前端 dev server 默认代理 `/api` 到 `http://127.0.0.1:8000`。

## 目录结构

```
├── frontend/          # React 前端
│   └── src/
│       ├── components/  # UI 组件
│       ├── pages/       # 页面
│       ├── store/       # Zustand 状态管理
│       └── types/       # TypeScript 类型
├── backend/           # FastAPI 后端
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── core/        # 核心逻辑 (LangGraph, DB, LLM)
│   │   └── scripts/     # 数据导入 / 爬虫脚本
│   └── tests/
└── .gitignore
```

## 功能

- 📋 虚拟滚动题库浏览（按难度/公司/标签筛选）
- 📝 题目详情（提示 / Markdown 答案 + 代码高亮）
- 📚 知识库文档引用（5 个 GitHub 仓库关联）
- 🤖 LangGraph 模拟面试（SSE 流式反馈）
- ⚙️ 管理面板（统计 + 爬取 + 编辑/删除）

## License

MIT
