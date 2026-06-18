#!/usr/bin/env python
"""
牛客网面经爬虫（Playwright）

策略：
1. 从牛客讨论区列表页（/discuss?type=2）按页翻页，收集面经帖子的 URL
2. 逐个访问帖子详情页，从正文中提取面试题（数字序号行）
3. 去重（按 source_url）后写入 SQLite

使用方式：
    # 命令行直接运行
    python -m app.scripts.crawl_nowcoder

    # 通过 API 触发
    POST /api/admin/crawl  {"max_pages": 5}

依赖：
    pip install playwright
    playwright install chromium
"""

import sys
import re
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.core.database import insert_question, log_crawl
from app.core.config import settings


def _classify_questions_batch(qs: list[dict]) -> list[dict]:
    """
    批量 LLM 分类（最佳效果）。LLM 不可用时 fallback 到启发式。
    原地修改并返回题目列表。
    """
    from app.core.config import settings

    titles = [q["title"] for q in qs]
    llm_results = [None] * len(qs)

    if settings.llm_enabled:
        try:
            from app.core.llm_client import get_llm_service
            svc = get_llm_service()
            import asyncio
            llm_results = asyncio.run(svc.batch_classify_questions(titles))
        except Exception:
            pass  # fallback below

    for i, q in enumerate(qs):
        r = llm_results[i] if i < len(llm_results) else None
        if r and isinstance(r, dict):
            q["difficulty"] = r.get("difficulty", _guess_difficulty(q["title"]))
            q["category"] = r.get("category", _guess_category(q["title"]))
            q["hint"] = r.get("hint", _generate_hint(q["title"]))
            q["expected_keywords"] = r.get("keywords", [])
        else:
            q["difficulty"] = _guess_difficulty(q["title"])
            q["category"] = _guess_category(q["title"])
            q["hint"] = _generate_hint(q["title"])
            q["expected_keywords"] = []
    return qs
    """根据题目标题推断难度"""
    t = title.lower()
    if any(kw in t for kw in ["区别", "设计", "架构", "优化", "源码", "原理", "为什么", "如何设计",
                               "底层", "怎么处理", "如何解决"]):
        return "hard"
    if any(kw in t for kw in ["流程", "实现", "怎么做", "如何做", "步骤", "方式", "如何理解"]):
        return "medium"
    return "easy"


def _guess_category(title: str) -> str:
    """根据题目标题推断分类"""
    t = title.lower()
    if any(kw in t for kw in ["rag", "检索", "向量", "知识库", "bm25", "embedding", "嵌入", "rerank"]):
        return "RAG"
    if any(kw in t for kw in ["mcp", "协议", "server", "server"]):
        return "MCP协议"
    if any(kw in t for kw in ["function call", "工具调用", "tool", "工具"]):
        return "Function Calling"
    if any(kw in t for kw in ["prompt", "提示词", "提示工程"]):
        return "Prompt Engineering"
    if any(kw in t for kw in ["记忆", "memory", "短期", "长期", "上下文"]):
        return "记忆机制"
    if any(kw in t for kw in ["模型", "model", "gpt", "claude", "llm", "大模型"]):
        return "模型架构"
    if any(kw in t for kw in ["react", "plan", "agent", "智能体", "规划", "编排", "任务"]):
        return "Agent基础"
    return "Agent基础"


def _generate_hint(title: str) -> str:
    """生成基础提示"""
    cat = _guess_category(title)
    hints = {
        "RAG": "从检索和生成两个核心环节展开，解释文档切片、向量化、相似度搜索和重排序的作用。",
        "MCP协议": "从能力协商、工具发现、工具调用三个步骤展开分析。",
        "Function Calling": "考虑 LLM 如何输出函数名和参数，以及结果如何返回给模型。",
        "Prompt Engineering": "从经典技术（Zero-shot/Few-shot/CoT/ReAct）出发，结合实际效果对比。",
        "记忆机制": "区分会话内上下文窗口和跨会话持久化存储的设计策略。",
        "模型架构": "从适配器模式、统一接口抽象、动态路由三个层次考虑。",
        "Agent基础": "从推理、决策、执行和工具调用的循环角度分析。",
    }
    for key, hint in hints.items():
        if key.lower() in cat.lower():
            return hint
    return "结合相关概念的定义、原理和实际应用场景来回答。"


def _clean_text(text: str) -> str:
    """清理 HTML 提取文本中的编码残留"""
    return (
        text.replace("\xa0", " ")       # HTML &nbsp; → 普通空格
        .replace("​", "")          # 零宽空格
        .replace("　", " ")         # 全角空格
        .replace("\r", "\n")            # CR → LF
        .strip()
    )


def _looks_like_agent_question(title: str) -> bool:
    """
    判断是否属于 Agent/AI 领域面试题。
    返回 False = 明显不是 Agent 领域的题目（Java 基础、Spring、SQL 等）。
    """
    t = title.lower()

    # 强烈 Agent/AI 信号 — 只要命中就算 Agent 面试题
    agent_signals = [
        "agent", "agentic", "智能体", "langchain", "langgraph", "llamaindex",
        "rag", "检索增强", "大模型", "llm", "gpt", "claude", "chatgpt",
        "prompt", "提示词", "提示工程", "function call", "tool call",
        "工具调用", "mcp", "model context protocol", "embedding", "向量",
        "rerank", "重排序", "chunk", "切片", "文档加载",
        "react", "plan-and-solve", "规划", "反思", "reflection",
        "multi-agent", "多智能体", "记忆机制", "短期记忆", "长期记忆",
        "上下文窗口", "token", "retrieval", "检索",
        "aigc", "生成式", "ai agent", "ai面试", "ai 面试",
    ]

    for sig in agent_signals:
        if sig in t:
            return True

    # 明确非 Agent 领域信号 — 判定为普通技术面试题，过滤掉
    non_agent_signals = [
        "java", "spring", "mysql", "sql", "redis", "rabbitmq", "kafka",
        "docker", "kubernetes", "k8s", "linux", "nginx", "tomcat",
        "jvm", "servlet", "mybatis", "hibernate", "oracle",
        "c++", "c语言", "c#", ".net", "php", "ruby",
        "设计模式", "单例", "工厂模式",
        "public", "private", "protected", "static关键字",
        "arraylist", "hashset", "linkedlist", "hashmap", "concurrenthashmap",
        "threadlocal", "synchronized", "reetrantlock", "aop", "ioc",
        "虚拟线程", "线程池", "线程安全",
        "tcp", "http", "socket", "网络协议",
        "排序算法", "二叉树", "链表", "动态规划", "leetcode",
        "内存对齐", "内存泄漏", "垃圾回收",
        "嵌入式", "单片机",
        "项目介绍", "自我介绍", "hr面", "hr 面",
        "gitee", "github", "代码仓库", "仓库链接",
        "双指针", "回溯", "dfs", "bfs", "滑动窗口", "动态规划",
        "期望薪资", "职业规划", "加班", "离职原因",
        "消息队列", "mq", "分布式锁", "redisson", "redlock",
        "锁升级", "锁粗化", "锁消除", "cas", "aqs",
        "连接池", "okhttp", "postdelay", "handler",
        "多线程", "并发", "thread", "线程", "进程",
        "springboot", "spring cloud", "dubbo", "zookeeper",
    ]

    # 如果没有命中 Agent 信号，且命中 ≥1 个非 Agent 信号，判定为非 Agent 题
    non_agent_count = sum(1 for sig in non_agent_signals if sig in t)
    if non_agent_count >= 1:
        return False

    # 默认保留（可能包含通用架构/设计题，人工审核时再判断）
    return True


def _split_concatenated_title(title: str) -> list[str]:
    """
    分离被拼接在一行中的多道题目。
    例如 "1. 线程池核心参数 2. ReetrantLock和Synchronized区别 3. 锁计数器"
    → 如果检测到内部序号，只取第一道。
    """
    # 检查是否有明显的内部序号（如 "2." "3、" 等跟在第一题后面）
    if re.search(r'(?:^.{0,80}?)\s+\d+\s*[\.\、\)）:：]\s*.{8,}', title):
        # 可能是多题拼接，尝试提取第一题
        # 找到第二个序号的位置，截断
        match = re.search(r'\s+(\d+)\s*[\.\、\)）:：]\s*.{8,}$', title)
        if match:
            first_q = title[:match.start()].strip()
            if len(first_q) >= 10:
                return [first_q]
        # 如果无法可靠分割，返回空（跳过整条）
        return []
    return [title]


def _title_has_boilerplate(title: str) -> bool:
    """检查标题是否包含牛客网 UI 残留文本"""
    boilerplate = [
        "查看更多", "查看原文", "收藏", "分享", "举报",
        "投递方式", "投递链接", "简历投递", "内推码",
        "笔试时间", "面试时间", "已编辑", "匿名用户",
        "关注问题", "写回答", "邀请回答",
    ]
    for bp in boilerplate:
        if bp in title:
            return True
    return False


def _extract_questions_from_post(text: str, source_url: str) -> list[dict]:
    """
    从面经帖子正文提取面试题。
    匹配模式：数字序号开头的行（1. / 1、/ 1) / Q1: 等）
    """
    text = _clean_text(text)
    questions = []

    # 按行处理，避免跨行匹配和内容粘连
    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 匹配序号开头的行：可能有前导换行
        match = re.match(r'\s*(\d+)\s*[\.\、\)）:：]\s*(.{10,250})', line)
        if not match:
            continue

        title = match.group(2).strip()

        # 清理标题末尾的 UI 残留
        title = re.sub(r'\s*[\.\。]{3,}\s*(查看更多|查看原文|详情).*$', '', title)

        # 过滤非题目的序号行
        skip_patterns = [
            r'^\d{4,}',              # 年份
            r'^[年月日周]',            # 日期/时间
            r'^实习|项目|自我|简单介绍',  # 非题目
            r'^牛客|^关注|^发布|^已编辑',  # 平台 UI
            r'^\d+[Kk]\s',            # 薪资
            r'^(投递|已投|面试时间|笔试时间|面试官|面试形式)',  # 流程信息
            r'^\d+月|\d+号面试|\d+日面',  # 日期描述
            r'吃青春饭|^都是',          # 灌水内容
            r'手写|code\s*也要',        # 非题目方向
            r'你平常|^平常|^平时',       # 闲聊
            r'错误假设|前置准备|基础业务',  # 笔记标题
            r'匿名|^从项目中',           # 非题目
            r'资格面试|^基于\s',         # 非典型面试题格式
            r'^对实习|^ai项目',          # 非题目
            r'干久了|一辈子|^(你是|你好|您好)',  # 灌水/打招呼
            r'^(群|面经关键词|面试复盘|总结)',  # 元信息条目
            r'^\d+年校招|^\d+届',       # 招聘年份描述
            r'^作者|^最后发布于|^发布于',  # 内容页元数据
        ]
        if any(re.match(sp, title) for sp in skip_patterns):
            continue

        # 题目长度过滤
        if len(title) < 10 or len(title) > 200:
            continue

        # 牛客 UI 残留检查
        if _title_has_boilerplate(title):
            continue

        # Agent 领域检查
        if not _looks_like_agent_question(title):
            continue

        # 多题拼接处理
        titles = _split_concatenated_title(title)
        for t in titles:
            questions.append({
                "title": t,
                "difficulty": "",  # 由 _classify_questions_batch 填充
                "category": "",    # 由 _classify_questions_batch 填充
                "hint": "",        # 由 _classify_questions_batch 填充
                "answer": f"## {t}\n\n（答案来自牛客网面经原帖，请查看原文获取完整讨论内容）",
                "source": "nowcoder",
                "source_url": source_url,
                "expected_keywords": [],  # 由 _classify_questions_batch 填充
            })

    # 批量 LLM 分类
    return _classify_questions_batch(questions)


def run_crawl(max_pages: int | None = None) -> tuple[int, int]:
    """
    执行牛客网爬取。

    返回: (pages_crawled, new_items_inserted)
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ImportError(
            "请先安装 Playwright: pip install playwright && playwright install chromium"
        )

    max_pages = max_pages or settings.crawl_max_pages
    delay = settings.crawl_delay_seconds
    total_new = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-gpu", "--no-sandbox"])
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        # 超时宽一些，应对网络波动
        page.set_default_timeout(30000)

        for page_num in range(1, max_pages + 1):
            try:
                url = f"https://www.nowcoder.com/discuss?type=2&order=0&page={page_num}"
                print(f"[crawl] 列表第 {page_num}/{max_pages} 页")

                page.goto(url, wait_until="domcontentloaded")
                time.sleep(delay + 1)  # 等 JS 渲染

                # 提取本页所有面经帖子 URL
                html = page.content()
                discuss_ids = set()
                for m in re.finditer(r'/discuss/(\d+)(?:\?[^\"\']*)?', html):
                    discuss_ids.add(m.group(1))

                print(f"[crawl]   发现 {len(discuss_ids)} 个帖子")

                # 逐个访问帖子
                for did in discuss_ids:
                    post_url = f"https://www.nowcoder.com/discuss/{did}"
                    # 去重检查
                    from app.core.database import get_connection
                    conn = get_connection()
                    existing = conn.execute(
                        "SELECT id FROM questions WHERE source_url = ?", (post_url,)
                    ).fetchone()
                    conn.close()
                    if existing:
                        continue

                    try:
                        page.goto(post_url, wait_until="domcontentloaded")
                        time.sleep(delay)

                        # 提取帖子正文
                        content_el = page.query_selector("[class*=content]")
                        if not content_el:
                            content_el = page.query_selector("body")
                        post_text = content_el.inner_text() if content_el else ""

                        if len(post_text) < 50:
                            continue

                        # 从正文提取面试题
                        company_tag = _extract_company(post_text)
                        qs = _extract_questions_from_post(post_text, post_url)
                        for q in qs:
                            q["company"] = company_tag if company_tag != "未知" else None
                            qid = insert_question(q)
                            if qid:
                                total_new += 1

                        if qs:
                            print(f"[crawl]   {did}: +{len(qs)} 题 [{company_tag}]")

                    except Exception as e:
                        print(f"[crawl]   帖子 {did} 出错: {e}")
                        continue

            except Exception as e:
                print(f"[crawl] 列表第 {page_num} 页出错: {e}")
                continue

        browser.close()

    log_crawl("nowcoder", max_pages, total_new)
    print(f"[crawl] 完成: {max_pages} 页, 新增 {total_new} 题")
    return max_pages, total_new


def _extract_company(text: str) -> str:
    """尝试从帖子正文提取公司名"""
    companies = [
        "字节跳动", "快手", "滴滴", "蚂蚁", "美团", "腾讯", "百度",
        "阿里", "阿里巴巴", "Shopee", "携程", "小红书", "拼多多",
        "网易", "京东", "华为", "小米", "哔哩哔哩", "知乎",
    ]
    found = []
    for c in companies:
        if c in text:
            found.append(c)
    return ", ".join(found[:3]) if found else "未知"


# ─── CLI 入口 ──────────────────────────────────────────

if __name__ == "__main__":
    pages, new_items = run_crawl()
    print(f"Done: {pages} pages, {new_items} new questions")
