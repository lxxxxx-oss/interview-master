# 服务器运维手册

> 最后更新：2026-06-19

## 服务器信息

| 项目 | 值 |
|------|-----|
| **域名** | devinterview.cn + www.devinterview.cn |
| **备用地址** | http://47.86.185.140（自动 301 重定向到域名） |
| **厂商** | 阿里云 ECS 香港 |
| **配置** | 2C2G / 40G SSD |
| **系统** | Alibaba Cloud Linux 3 (OpenAnolis) |
| **DNS 托管** | 阿里云云解析 DNS |

---

## 安全防护配置

### Fail2Ban — SSH 防暴力破解

```bash
systemctl status fail2ban                             # 查看运行状态
fail2ban-client status sshd                           # 查看 SSH 防护统计
fail2ban-client status sshd | grep "Currently banned" # 当前封禁 IP 数
journalctl -u fail2ban -f                             # 实时日志
```

**规则：** 10 分钟内 SSH 密码错误 3 次 → 封禁 IP 2 小时

### Nginx 限流规则

```bash
grep limit /etc/nginx/conf.d/interview-master.conf   # 查看限流配置
grep " 429 " /var/log/nginx/access.log               # 查看被限流的请求
```

| 限流目标 | 规则 | 说明 |
|---------|------|------|
| `/api/` | 10 req/s + burst 20 | 防止 API 被刷 |
| 全局 | 30 req/s + burst 50 | 防止爬虫滥用 |
| 连接数 | 单 IP 最多 20 并发 | 防止连接耗尽 |

超过限制 → 返回 HTTP 429 Too Many Requests

### 端口暴露

| 端口 | 用途 | 开放范围 |
|------|------|---------|
| 22 | SSH | 阿里云安全组管控 |
| 80 | HTTP | 全网 |

### 容量评估

| 指标 | 数值 |
|------|------|
| CPU | 2 核 Intel Xeon Platinum |
| 内存 | 2GB（可用 ~1.4GB） |
| 带宽 | 阿里云按量计费 |
| Nginx 并发 | 1024 worker × auto 进程 |
| 预计承载 | **~500-1000 并发用户**（瓶颈在带宽） |

---

## 服务管理

### 后端服务 (FastAPI)

```bash
systemctl status interview-master       # 查看状态
systemctl restart interview-master      # 重启
systemctl stop interview-master         # 停止
systemctl start interview-master        # 启动
journalctl -u interview-master -f       # 查看实时日志
```

### Nginx

```bash
systemctl status nginx                  # 查看状态
systemctl reload nginx                  # 重载配置（不中断服务）
systemctl restart nginx                 # 重启
nginx -t                                # 测试配置是否合法
```

### 路径一览

| 用途 | 路径 |
|------|------|
| 项目代码 | `/opt/interview-master/` |
| 前端构建产物 | `/opt/interview-master/frontend/dist/` |
| 题库数据库 | `/opt/interview-master/backend/data/questions.db` |
| Nginx 配置 | `/etc/nginx/conf.d/interview-master.conf` |
| Nginx 访问日志 | `/var/log/nginx/access.log` |
| Nginx 错误日志 | `/var/log/nginx/error.log` |
| GoAccess 统计页面 | `/opt/interview-master/stats/index.html` |
| Systemd 服务文件 | `/etc/systemd/system/interview-master.service` |

---

## 更新部署流程

```bash
# 1. 拉取最新代码
cd /opt/interview-master
git pull

# 2. 重新构建前端
cd /opt/interview-master/frontend
npm install          # 如果 package.json 有变更
npm run build

# 3. 重启后端（如果后端代码有变更）
systemctl restart interview-master

# 4. 确认服务正常
curl -s http://127.0.0.1:8000/api/stats
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/
```

> **注意：** 生产构建自动读取 `frontend/.env.production`，其中 `VITE_ENABLE_INTERVIEW=false` 会隐藏模拟面试的前端入口（路由 + 导航栏）。如需恢复模拟面试，将此值改为 `true` 后重新构建前端即可。

---

## 前端环境变量

| 文件 | 用途 |
|------|------|
| `frontend/.env.production` | 生产构建时生效，`VITE_ENABLE_INTERVIEW=false` 隐藏模拟面试 |
| `frontend/.env.development` | 本地开发时生效，`VITE_ENABLE_INTERVIEW=true` 保留完整功能 |

变量说明：

| 变量 | 值 | 说明 |
|------|-----|------|
| `VITE_ENABLE_INTERVIEW` | `true` / `false` | 控制模拟面试前端入口（路由 + 导航栏） |
| `VITE_ENABLE_ADMIN` | `true` / `false` | 控制管理页前端入口（目前未启用） |

---

## 知识库引用系统

### 架构

题库中的每道题通过 `code_references` 表关联 5 个技术开源仓库的文档文件。引用策略为**关键词匹配 Top-K**，在导入时计算相关性分数并持久化，前端按分数降序展示。

### 数据源（5 个知识库）

| 仓库 | 覆盖主题 |
|------|----------|
| `datawhalechina/hello-agents` | Agent 基础、模型架构、Prompt Engineering、记忆机制 |
| `datawhalechina/all-in-rag` | RAG、向量检索 |
| `datawhalechina/easy-vibe` | Agent 基础、Prompt Engineering、Function Calling |
| `shareAI-lab/learn-claude-code` | Agent 基础、MCP 协议、Function Calling、记忆机制 |
| `xindoo/agentic-design-patterns` | 全 8 类覆盖（Agent Design Patterns 中文版） |

### 关键词库（8 类，共 ~130 个）

每个技术类别维护一个关键词集合，用于评分匹配：

| 分类 | 代表性关键词 |
|------|--------------|
| **RAG** | RAG, 检索增强, chunk, embedding, 向量数据库, Milvus, FAISS, 召回, retrieval |
| **Agent 基础** | Agent, ReAct, Plan-and-Solve, Multi-Agent, 编排, 状态机, 工作流, workflow |
| **MCP 协议** | MCP, Model Context Protocol, 工具注册, Server, 动态发现 |
| **Function Calling** | Function Call, 工具调用, Tool Use, 参数解析, API |
| **记忆机制** | 记忆, context, session, 持久化, 短期记忆, 长期记忆, 衰减 |
| **Prompt Engineering** | Prompt, 提示链, CoT, ToT, 推理, 指令, 引导, 模板 |
| **模型架构** | LLM, Transformer, 模型切换, 路由, Router, 抽象层, 适配 |
| **向量检索** | 向量, embedding, 相似度, ANN, FAISS, Milvus, cosine, 距离 |

### 相关性评分算法

```
score = A × 0.30 + B × 0.30 + C × 0.30 + D × 0.10
```

| 符号 | 名称 | 权重 | 计算方式 |
|------|------|------|----------|
| A | 标题命中率 | 30% | 题目关键词在文件描述/路径中的命中比例 |
| B | 答案命中率 | 30% | 答案关键词在文件描述/路径中的命中比例 |
| C | 文件覆盖度 | 30% | 文件关键词在题目（标题+答案）中的覆盖比例 |
| D | 分类匹配度 | 10% | 文件描述中包含题目分类关键词的比例 |

**关键词提取**：从 `KEYWORD_MAP` 中按题目分类取出关键词集合，分别在题目和文件文本中执行子串匹配。中文不进行分词，直接按词库子串匹配（避免分词引入的误差）。

### 引用筛选策略

| 参数 | 值 | 说明 |
|------|-----|------|
| Top-K | 8 | 每道题最多关联 8 条引用 |
| 最低阈值 | 0.05 | 分数低于此值不关联 |
| 同分类匹配 | 优先 | 先匹配同分类文件 |
| 跨分类回退 | 兜底 | 同分类全 < 0.05 时尝试所有文件 |

### 答案内联锚点

`_build_reference_anchors()` 在 API 查询时实时分析引用描述与答案文本的匹配位置：

1. 从引用描述中提取关键词（前 8 个有意义的词）
2. 在答案中查找每个关键词的首次出现位置
3. 统计每个候选位置附近（前后 100 字符窗口）的关键词密度
4. 选取密度最高且 >= 2 个关键词命中的位置作为锚点
5. 相邻 30 字符内的锚点去重，保留 score 最高的
6. 返回 `[{refId, score, snippet, position}]`

### 前端展现规则

| 指标 | 规则 |
|------|------|
| 排序 | 按 score 降序 |
| 折叠 | 默认展示 Top 3，其余通过「展开全部 N 条引用」按钮展开 |
| 高相关 | score > 0.28 → 🟢 高相关标签 |
| 中相关 | 0.12–0.28 → 🟠 中相关标签 |
| 低相关 | < 0.12 → 不显示标签 |
| 答案锚点 | `referenceAnchors` 生成 `[1]` `[2]` 编号按钮，点击滚动到对应卡片 |
| 卡片高亮 | 点击锚点后 2 秒蓝色 `ring-2` 高亮动画 |

### 引用维护

```bash
# 重建全部引用（清空旧 + 重新匹配）
cd /opt/interview-master/backend
python3 -m app.scripts.import_references_keyword --clear --top-k 8

# 预览（不写库）
python3 -m app.scripts.import_references_keyword --dry-run --top-k 8

# 添加新知识库文件：
# 1. 编辑 app/scripts/import_references.py 中的 KNOWLEDGE_BASES
# 2. 编辑 app/scripts/import_references_keyword.py 中的 KEYWORD_MAP（如需）
# 3. 运行上述 rebuild 命令
```

## 查看访问统计

### 方式一：百度统计（推荐日常使用）

打开 [百度统计后台](https://tongji.baidu.com/)，登录后查看：
- 📊 PV/UV/跳出率
- 🌍 访问者地域分布
- 📱 设备类型占比
- 🔗 来源渠道
- 📄 热门页面排行

### 方式二：GoAccess HTML 报告

浏览器访问：**http://devinterview.cn/stats/**

登录凭据：`admin` / `interview2026!`

页面每 10 分钟自动刷新一次（crontab 驱动）。

### 方式三：命令行实时面板

SSH 登录后：

```bash
goaccess /var/log/nginx/access.log --log-format=COMBINED
# 或
goaccess-web live
```

按 F5 刷新，按 q 退出。

### 方式四：直接查 Nginx 日志

```bash
# 实时流量
tail -f /var/log/nginx/access.log

# 今日 PV
wc -l /var/log/nginx/access.log

# 今日 UV
awk '{print $1}' /var/log/nginx/access.log | sort -u | wc -l

# Top 10 访问 IP
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -10

# Top 10 页面
awk '{print $7}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -10

# 一键统计脚本
echo "=== 访问统计 ===" \
  && echo "总 PV: $(wc -l < /var/log/nginx/access.log)" \
  && echo "独立 UV: $(awk '{print $1}' /var/log/nginx/access.log | sort -u | wc -l)" \
  && echo "热门页面 Top 5:" \
  && awk '{print $7}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -5
```

---

## 密码管理

| 场景 | 用户名 | 密码 |
|------|--------|------|
| SSH 登录 | root | `17723273016Lx` |
| 统计面板 (/stats) | admin | `interview2026!` |

> ⚠️ 强烈建议修改 SSH 密码为强密码，或改用 SSH 密钥登录并禁用密码认证。
