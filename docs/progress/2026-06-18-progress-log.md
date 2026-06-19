# 开发进度日志

## 2026-06-19 深夜 — 暗色模式（已回滚）
- Tailwind v4 class-based dark mode (`@custom-variant dark`) 与 Ant Design `darkAlgorithm` 配合存在兼容性问题，已回滚
- 问题根因：Tailwind v4 默认 `prefers-color-scheme` media query，需 `@custom-variant dark` 切换到 class 模式，但 Ant Design 的主题切换与 Tailwind dark: 类的交互仍有样式冲突
- 已通过 `git checkout` 恢复所有组件到暗色模式前的状态，后续重新评估方案

## 2026-06-19 晚上 — 搜索增强：SQLite FTS5 全文搜索
- **Flashcard** — `dark:border-gray-700 dark:hover:border-blue-500`
- **QuestionDetail** — 标题 `dark:text-gray-100`
- Ant Design 组件（Card/Tag/Menu/Collapse 等）由 ConfigProvider 自动适配暗色

## 2026-06-19 晚间 — 知识库引用增强
- **score 字段** — `code_references` 表新增 `score` 列，存储关键词匹配分数（0-1）
- **后端排序** — `get_question()` 返回引用按 score 降序，优先展示高相关引用
- **导入脚本** — `import_references_keyword.py` 写入 score 到数据库
- **答案锚点** — `_build_reference_anchors()` 分析引用描述与答案的匹配位置，生成 inline anchors
- **前端引用区域重设计** — `ReferencesSection` 组件：按 score 排序、相关度标签（高/中/低）、编号锚点 `[N]`、点击滚动高亮
- **折叠展开** — 默认显示 Top 3，其余用「展开全部 N 条引用」按钮
- **Python 3.6 兼容** — `config.py` + `database.py` + `import_references_keyword.py` 类型注解改用 typing 模块
- 服务器引用已重建（236/243 题，1308 条带分引用）

## 2026-06-19 傍晚 — 移动端适配优化
- **Flashcard 提示按钮** — trigger 从 `hover` 改为 `click`，按钮始终可见，移动端可点击弹出
- **卡片内边距** — 响应式 `14px 16px`（mobile）→ `16px 20px`（sm+）
- **标题字号** — 响应式 `14px`（mobile）→ `15px`（sm+）
- **QuestionGrid 卡片高度** — 移动端 200px（桌面 220px），`useState` + `resize` 监听动态切换
- **FilterBar** — 输入框/下拉框宽屏固定宽度 + 窄屏 `w-full` `maxWidth`，Space `gap-4` 手机间距收紧
- 状态提示文字响应式 `10px`→`11px`，移除学习状态下拉多余的 `size="small"`

## 2026-06-19 下午 — 搜索增强：SQLite FTS5 全文搜索
- `backend/app/core/database.py` — 新增 `questions_fts` FTS5 虚拟表（索引 title/answer/hint/category/expected_keywords）
- FTS5 触发器（INSERT/UPDATE/DELETE）保持索引与 questions 表自动同步
- `get_connection()` 启动时自动检测并填充 FTS 索引（首次启用/数据不一致时）
- `list_questions()` 新增 `search_type` 参数：`fts`（默认，BM25 相关性排序）或 `like`（旧方案回退）
- `_escape_fts_query()` 转义用户输入中的 FTS 语法特殊字符
- `backend/app/api/interview.py` — `/api/questions` 端点新增 `search_type` 参数
- `backend/scripts/init_fts.py` — FTS 手动初始化/重建脚本
- 前端零改动，搜索结果质量显著提升
- 服务器已部署验证通过

### FTS vs LIKE 对比
| 搜索词 | FTS 结果 | LIKE 结果 | 效果 |
|--------|----------|-----------|------|
| RAG | 47 | 46 | 相当 |
| function calling | 19 | 17 | FTS 多找到 2 条相关题（answer/hint 命中） |
| memory cache | 1 | 0 | FTS 打破单词边界，LIKE 无法跨词匹配 |
| 向量检索 | 10 | 10 | 相当 |

## 2026-06-19 — 模拟面试功能上线开关
- 引入 Vite 环境变量 `VITE_ENABLE_INTERVIEW` 控制模拟面试功能的前端入口
- `frontend/.env.production` — 设置 `VITE_ENABLE_INTERVIEW=false`，生产构建隐藏模拟面试
- `frontend/.env.development` — 设置 `VITE_ENABLE_INTERVIEW=true`，本地开发保留完整功能
- `frontend/src/vite-env.d.ts` — TypeScript 类型声明，支持 `import.meta.env` 智能提示
- `App.tsx` — 路由改为条件注册：`ENABLE_INTERVIEW` 为 false 时不注册 `/interview` 路由
- `AppLayout.tsx` — 导航菜单改为条件渲染：`ENABLE_INTERVIEW` 为 false 时隐藏「模拟面试」导航项
- 后端 API 保留不动 — `/api/interview/*` 仍可调用，只是前端不展示入口
- 管理页路由/导航项也改为环境变量模式（注释留用，后续可启用 `VITE_ENABLE_ADMIN`）
- 验证通过：生产构建产物中无 `/interview` 路由注册、无 `VITE_ENABLE_INTERVIEW` 变量残留

## 2026-06-18 下午 — UI 优化与提示系统
- Flashcard 来源图标移除、Hint 按钮中文化、hover 触发弹出、题目详情页来源标签移除
- 首页声明文案优化（"聚焦高频真题""答案由 AI 生成仅供参考"）
- 243 道题目提示全面重写：从泛泛的"思考逻辑"改为有针对性的答题框架引导
- `generate_tailored_hint()` 嵌入 `database.py`，新题入库自动生成高质量提示
- 部署流程改为 scp 直传服务器（GitHub push 网络不稳）

## 2026-06-18 傍晚 — 上下题导航重构
- QuestionDetail 页面：上一题/下一题从顶部栏右上角改为左右两侧固定浮动导航
- **视觉** — 蓝色药丸按钮 (`#1677ff`)，标配文字 "上一题" / "下一题"，贴屏幕边缘，半圆角
- **交互** — `fixed` 居中 + 阴影，hover 加深扩宽，首题/末题自动透明隐藏
- **逻辑** — 使用 `filteredQuestions` 而非 `questions`，导航始终尊重当前筛选条件
- 直接 URL 进入详情页时自动并行加载列表，确保上下题按钮可正常工作

## 2026-06-18 上午 — 虚拟列表 + 无限滚动 + Bug 修复
- @tanstack/react-virtual 替代分页，无限滚动每次 50 道
- 搜索防抖 300ms，搜索时按标题命中权重排序
- 删除题目白屏 Bug 修复：DELETE 后即时更新 Zustand state
- 虚拟列表 onChange 改为 window scroll 事件监听

## 2026-06-17/18 — 品牌重构 + Hub 导入 + 知识库引用
- 品牌名「Agent 面试通」→「面试通」
- Hub 面经导入脚本 + 96 题入库
- 知识库引用修复：重建 code_references 表，3034 条引用全覆盖
