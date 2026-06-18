# 面试通 (Interview Master)

面向 AI Agent 领域的面试题库平台，已收录 **243 道**面试真题。

> 🌐 [devinterview.cn](http://devinterview.cn)

## 功能

- 📋 题库浏览（难度/公司/标签筛选 + 搜索 + 虚拟滚动无限加载）
- 📝 题目详情（个性化解题提示 / Markdown 答案 + 代码高亮 + 知识库引用）
- 🤖 模拟面试 & 管理后台（已实现，即将上线）

## 技术栈

React 18 + TypeScript + Ant Design + Zustand + FastAPI + SQLite + LangGraph

## 本地开发

```bash
# 后端
cd backend && pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend && npm install && npx vite
```

## 知识库引用 · 致谢

本项目关联了以下开源知识库的文档引用，帮助学习者快速定位官方资料：

| 仓库 | 作者/组织 | 说明 |
|------|----------|------|
| [hello-agents](https://github.com/datawhalechina/hello-agents) | Datawhale | 从零构建智能体 |
| [all-in-rag](https://github.com/datawhalechina/all-in-rag) | Datawhale | RAG 技术全栈指南 |
| [easy-vibe](https://github.com/datawhalechina/easy-vibe) | Datawhale | Vibe Coding 教程 |
| [learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) | shareAI-lab | Agent Harness 从零实现 |
| [agentic-design-patterns](https://github.com/xindoo/agentic-design-patterns) | xindoo | Google Agent 设计模式 |

**声明**：知识库引用功能仅提供 GitHub 文件链接跳转，不复制或分发任何仓库内容。如涉及侵权请通过 GitHub Issue 联系，会立即处理。

## License

MIT
