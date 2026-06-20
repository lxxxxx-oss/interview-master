# AI 面试通 — 项目整体实现状态

> 最后更新：2026-06-19（提交 c13fab2 已推送 GitHub）

## 第一阶段：知识库展示（Frontend UI）✅

- [x] React 18 + TypeScript + Vite + Ant Design + Tailwind CSS + Zustand
- [x] **虚拟列表替代分页** — @tanstack/react-virtual 窗口级虚拟滚动
- [x] 题目详情页 — 折叠面板独立展开提示/答案
- [x] Markdown 渲染 + Prism.js 代码高亮（oneDark）
- [x] 知识库 GitHub 文档引用（1308 条带分，236/243 题覆盖）
- [x] 管理页：统计 + 爬取面板 + 知识库状态
- [x] 路由：`/` → 首页, `/question/:id` → 详情, `/interview` → 模拟面试, `/admin` → 管理
- [x] 前端已对接后端真实 API（替换 Mock 数据）
- [x] **Flashcard UI 优化** — 移除遮罩 hover，Hint Popover 侧边展示，卡片点击直入详情
- [x] **FilterBar 修复** — "不限"选项，可清空筛选
- [x] **品牌重构** — Agent 面试通 → AI 面试通，QuestionCategory 扩展为 string 类型
- [x] **GitHub 发布** — [lxxxxx-oss/interview-master](https://github.com/lxxxxx-oss/interview-master)

---

## 第二阶段：后端面试工作流 ✅

- [x] FastAPI + LangGraph 后端
- [x] SQLite 持久化存储（questions, code_references, crawl_log）
- [x] 环境变量统一配置（`app/core/config.py`）
- [x] 面经 Markdown 解析导入脚本（73 题）
- [x] 面试工作流：Question → Evaluate → Critique（追问循环）
- [x] SSE 流式 API
- [x] 题库 API：筛选、分页、详情、统计
- [x] 管理 API：`POST /api/admin/crawl`
- [x] 7 个单元测试全部通过
- [x] 牛客网爬虫深度修复
- [x] Agnes LLM 全栈集成：LLM-as-Judge + 自动分类 + 流式对话
- [x] 全题库 LLM 答案生成

---

## 第三阶段：流式对话 UI ✅

- [x] `/interview` 页面 — ChatGPT 风格聊天界面
- [x] SSE 流式消费 — fetch + ReadableStream 解析
- [x] 流式 token 逐字渲染 + Markdown + 代码高亮
- [x] 评估卡片 — 分数圆环 + 命中/遗漏关键词
- [x] 取消流式输出 + 面试设置页

## 第四阶段：题目管理 + 知识库引用修复 ✅

- [x] 知识库引用路径全面修复 — GitHub API 验证 5 个仓库实际文件结构
- [x] SQLite 数据层扩展 — `update_question`, `delete_question`（级联删除）
- [x] 管理 API — `PUT/DELETE /api/admin/questions/{id}` + 权限预留
- [x] 前端编辑/删除 UI — 详情页 Edit/Delete + 首页卡片管理入口
- [x] Flashcard UI 重设计 — Hint Popover、干净卡片、一键详情
- [x] 删除白屏修复 — 先导航再删除 + 404 友好提示
- [x] agent-interview-hub 面经导入 — 96 题（14 家公司 + 通用知识）
- [x] **编辑/删除 UI 隐藏** — 生产环境前端禁用，API 保留（curl/Postman 可调用）

---

## 第六阶段：用户交互优化 ✅

- [x] **题目状态标记** — 每道题支持「已学会 (✅)」和「收藏 (⭐)」两种状态，localStorage 持久化
- [x] **状态筛选** — FilterBar 新增「学习状态」下拉：未学(默认，排除已学会) / 全部 / 收藏 / 已学会
- [x] **卡片状态按钮** — Flashcard 底部左侧常驻状态图标，点击切换标记/取消，刷新不丢失
- [x] **详情页状态按钮** — QuestionDetail 标题区同步展示状态按钮
- [x] **声明文案更新** — 首页 + README + 知识库引用区均添加版权/免责声明
- [x] **提示系统优化** — 243 题提示全面重写 + 新题自动生成（`database.py:generate_tailored_hint()`）
- [x] **题目详情增强** — 标题区展示「考察点」关键词标签，帮助用户了解评分维度
- [x] **UI 细节修复** — 来源图标/标签移除、Hint 按钮中文化 + hover 触发、文档结构清理
- [x] **上下题导航重构** — 右侧小按钮→左右两侧蓝色浮动药丸，贴边醒目，筛选条件感知，支持直链进入
- [x] **模拟面试上线开关** — Vite 环境变量 `VITE_ENABLE_INTERVIEW` 控制前端入口，生产构建隐藏模拟面试路由+导航
- [x] **搜索增强** — SQLite FTS5 全文搜索（BM25），替换 LIKE 子串匹配，支持跨词搜索
- [x] **移动端适配** — 提示按钮 click 触发、响应式卡片高度/内边距/字号、FilterBar 宽窄屏自适应
- [x] **知识库引用增强** — score 评分排序、答案内联锚点、相关度标签、折叠展开

---

## 第七阶段：知识库引用增强 ✅

- [x] **引用评分** — `code_references` 表新增 `score` 字段，存储关键词匹配综合分数（0-1）
- [x] **评分算法** — 四维加权：标题命中(30%) + 答案命中(30%) + 文件覆盖度(30%) + 分类匹配度(10%)
- [x] **Top-K 筛选** — 每道题最多 8 条引用，最低阈值 0.05，同分类优先 + 跨分类回退
- [x] **答案锚点** — `_build_reference_anchors()` 实时分析引用描述与答案的匹配位置，生成 `referenceAnchors`
- [x] **前端重设计** — 引用按 score 排序、`[N]` 编号锚点、高/中/低相关度标签、默认折叠 Top 3
- [x] **点击联动** — 点击答案锚点按钮 → 滚动到对应引用卡片 + 2 秒蓝色高亮动画
- [x] **Python 3.6 兼容** — 全后端类型注解改用 `typing` 模块（服务器 Python 3.6.8）
- [x] **文档完善** — API.md + ops-manual.md 详列评分算法、关键词库、展现规则

---

## 第八阶段：暗色模式（已回滚）

Tailwind v4 class-based dark mode + Ant Design darkAlgorithm 组合存在样式冲突，已回滚所有暗色模式代码。`App.tsx`/`AppLayout.tsx`/`index.css` 已恢复到暗色模式前的状态。

- 根因：Tailwind v4 默认用 `prefers-color-scheme` media query，需 `@custom-variant dark` 切换到 class 模式，但 `dark:` 前缀类与 Ant Design 自动暗色计算后的 token 颜色存在双重叠加
- 后续方案：需要统一用一种暗色机制（要么纯 Tailwind，要么纯 Ant Design），不能混用

---

## 第五阶段：生产部署 + 域名 ✅

- [x] 阿里云 ECS 香港节点部署（2C2G / 40G / Alibaba Cloud Linux 3）
- [x] 域名注册与绑定 — **devinterview.cn**（¥29/年）+ www.devinterview.cn
- [x] Nginx 反向代理 + 静态文件托管 + IP 自动 301 重定向到域名
- [x] Systemd 服务 `interview-master.service`（开机自启 + 异常自动重启）
- [x] 百度统计接入（ID: `21f3a05b2d1661e141d10dd148af1adc`）
- [x] GoAccess 实时统计面板（`/stats`，HTTP Basic Auth，每 10 分钟刷新）
- [x] 运维文档编写 — `docs/2026-06-18-ops-manual.md`

---

## 数据统计

| 来源 | 数量 |
|------|------|
| 本地面经 (local) | 68 |
| 牛客网 (nowcoder) | 81 |
| Hub 面经 (hub) | 94 |
| **合计** | **243** |

| 引用 | 数量 |
|------|------|
| code_references | **1308**（带 score，Top-8/题） |
| 引用覆盖率 | 236/243 (97.1%) |

| **2026-06-19** | 搜索增强 FTS5 + 移动端适配 + 引用增强 + 暗色回滚 | 1308 条带分引用 |

## 线上地址

- 🌐 **devinterview.cn** — 生产环境
- 📊 **devinterview.cn/stats/** — 统计面板（admin / interview2026!）
- 📈 **百度统计** — tongji.baidu.com（ID: `21f3a05b2d1661e141d10dd148af1adc`）

## 已知问题

1. ~~GitHub 引用链接 404~~ ✅ 已修复
2. ~~知识库引用缺失（Hub 面经无引用）~~ ✅ 已修复
3. ~~删除题目白屏~~ ✅ 已修复
4. ~~无域名~~ ✅ 已购买 devinterview.cn
5. 无 HTTPS — 待配 Let's Encrypt
6. 评估仍是关键词匹配 — LLM-as-Judge 已实现但默认关闭
7. 会话存内存 — `sessions = {}`，服务器重启即丢失
8. 权限方案为临时 header 方案，后续需升级为 JWT/OAuth2 登录系统
9. ~~Git push 阻塞 — 本地 commit 未推送到 GitHub（网络问题）~~ ✅ 已推送（8d0d9e9）
10. ~~知识库引用无评分排序~~ ✅ 已实现 — score 降序 + 锚点标注
11. 在线地址未强制 HTTPS 重定向 — 待配证书后加入
12. 暗色模式 — 已尝试 Tailwind v4 dark: + Ant Design darkAlgorithm 混用存在样式冲突，已回滚。后续用纯 Tailwind 方案（不用 Ant Design darkAlgorithm）重新实现
13. ~~Git push 阻塞~~ ✅ 已推送 — 提交 8d0d9e9 已同步到 GitHub remote

## 文档规范

- `docs/progress/` — 每个大更新 (token > 10k) 一个文件，最多 10 个，超出删最早
- `docs/IMPLEMENTATION_STATUS.md` — 项目整体状态，走完里程碑更新
- `docs/API.md` — API 变更同步更新

## 待开始

- [ ] 暗色模式（纯 Tailwind 方案重新实现，不用 Ant Design darkAlgorithm）
- [ ] 牛客网爬虫定期增量运行
- [ ] 面试会话持久化（Redis）
- [ ] 正式登录系统（JWT/OAuth2）
