# AI 面试通 (Interview Master) — CLAUDE.md

## 重要规则

1. **文档仅存本地** — `docs/`、`需求文档.md`、progress logs、ops manuals 只存本地，绝不 push 到 GitHub（.gitignore 已配置）。详细原因见 memory [[docs-are-local-only]]
2. **不要使用 Workflow 工具** — 单线程协作即可，不需要多 agent 编排
3. **代码变更后需同步到服务器** — 修改前端/后端代码后，提醒是否需要同步到阿里云 ECS (47.86.185.140)
4. **记录每次变更** — 每次操作完成后写入 `docs/progress/` 中，更新 `docs/2026-06-18-ops-manual.md`

## 项目概要

- 名称：AI 面试通
- 域名：devinterview.cn
- 仓库：https://github.com/lxxxxx-oss/interview-master
- 服务器：阿里云 ECS 香港 2C2G (47.86.185.140)
- 技术栈：React 18 + TypeScript + FastAPI + SQLite + LangGraph

## 当前状态

- 243 道题，924 条知识库引用（关键词匹配 Top-K）
- 编辑/删除功能已在前端隐藏，API 保留
- 百度统计 + GoAccess 统计面板已配置
- Fail2Ban + Nginx 限流已配置
- 运维文档：`docs/2026-06-18-ops-manual.md`

## 交互偏好

- 用中文交流
- 操作前先确认，尤其是涉及服务器的操作
- 不要主动 push 到 GitHub（网络问题频繁）
