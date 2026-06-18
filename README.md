# 面试通 (Interview Master)

面向 AI 方向的面试题库平台，已收录 **248 道**面试真题（14 家公司 + 通用知识）。

> **当前版本**：v0.1（公测中）  
> 模拟面试、管理面板功能仍在开发中，暂未上线。

## 已收录公司

OpenAI、字节跳动、阿里巴巴、腾讯、百度、小红书、快手、美团、蚂蚁集团、华为、微软、谷歌、商汤科技、初创公司 + 通用知识

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 18 + TypeScript + Ant Design + Zustand + Tailwind CSS |
| 后端 | Python + FastAPI + SSE 流式 API |
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
| LLM_ENABLED | false | 启用 LLM 评估（开发中） |

### 前端

```bash
cd frontend
npm install
npx vite
```

前端 dev server 默认代理 `/api` 到 `http://127.0.0.1:8000`。

## 功能

- 📋 虚拟滚动题库浏览（按难度/公司/标签筛选）
- 📝 题目详情（提示 / Markdown 答案 + 代码高亮）
- 📚 知识库文档引用（5 个 GitHub 仓库关联）
- 🤖 模拟面试（开发中，暂未上线）
- ⚙️ 管理面板（开发中，暂未上线）

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

## 知识库引用 · 致谢

本项目部分面试题关联了以下开源知识库的文档引用，帮助学习者快速定位官方资料。

衷心感谢这些仓库的作者和维护者：

| 仓库 | 作者 / 组织 | 说明 |
|------|------------|------|
| [hello-agents](https://github.com/datawhalechina/hello-agents) | Datawhale | 从零构建智能体教程 |
| [all-in-rag](https://github.com/datawhalechina/all-in-rag) | Datawhale | RAG 技术全栈指南 |
| [easy-vibe](https://github.com/datawhalechina/easy-vibe) | Datawhale | Vibe Coding 教程 |
| [learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) | shareAI-lab | Agent Harness 从零实现 |
| [agentic-design-patterns](https://github.com/xindoo/agentic-design-patterns) | xindoo | Google Agent 设计模式中文版 |

**声明**：本项目的知识库引用功能仅提供 GitHub 文件链接跳转，帮助用户快速查阅相关文档片段。我们不复制、修改或分发上述仓库的任何内容。如果任何仓库作者认为引用方式不当或涉及侵权，请通过 GitHub Issue 联系我，我会立即调整或下架相关引用功能。

## License

MIT
