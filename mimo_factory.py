#!/usr/bin/env python3
"""
MiMo Content Factory - 有意义的内容生产系统
目标: 6天内用完 38B tokens，生成有价值的内容
"""

import asyncio
import aiohttp
import json
import time
import random
import os
import sys
from datetime import datetime
from pathlib import Path

# ============ 配置 ============
API_BASE = "https://token-plan-cn.xiaomimimo.com/v1"
API_KEY = os.environ.get("CUSTOM_API_KEY", "")
MODEL = "mimo-v2.5-pro"

CONCURRENCY = 50
MAX_OUTPUT_TOKENS = 8000
TOTAL_TARGET = 38_000_000_000
DAYS = 6

# 输出目录
OUTPUT_DIR = Path(__file__).parent / "output"
STATS_FILE = Path(__file__).parent / "factory_stats.json"
LOG_FILE = Path(__file__).parent / "factory_log.txt"

# ============ 内容模板 ============

# 知识工程 (30%)
KNOWLEDGE_TASKS = [
    # 科技百科
    {"category": "knowledge/tech", "topic": "量子计算原理与应用", "target": "万字深度解析"},
    {"category": "knowledge/tech", "topic": "人工智能发展史", "target": "完整时间线"},
    {"category": "knowledge/tech", "topic": "区块链技术架构", "target": "技术白皮书"},
    {"category": "knowledge/tech", "topic": "5G/6G通信技术", "target": "技术详解"},
    {"category": "knowledge/tech", "topic": "生物信息学", "target": "学科综述"},
    
    # 医学健康
    {"category": "knowledge/medical", "topic": "基因编辑技术CRISPR", "target": "科普长文"},
    {"category": "knowledge/medical", "topic": "精准医疗发展", "target": "行业报告"},
    {"category": "knowledge/medical", "topic": "中医药现代化", "target": "研究综述"},
    
    # 历史文化
    {"category": "knowledge/history", "topic": "中国古代科技史", "target": "系列文章"},
    {"category": "knowledge/history", "topic": "工业革命影响", "target": "深度分析"},
    {"category": "knowledge/history", "topic": "数字时代演变", "target": "趋势报告"},
    
    # 商业经济
    {"category": "knowledge/business", "topic": "全球供应链分析", "target": "研究报告"},
    {"category": "knowledge/business", "topic": "创业方法论", "target": "实战指南"},
    {"category": "knowledge/business", "topic": "数字营销策略", "target": "操作手册"},
]

# 代码生成 (25%)
CODE_TASKS = [
    # Web 开发
    {"category": "code/web", "project": "电商平台", "stack": "Next.js + Stripe"},
    {"category": "code/web", "project": "社交网络", "stack": "React + GraphQL"},
    {"category": "code/web", "project": "内容管理系统", "stack": "Vue.js + Node.js"},
    
    # 后端服务
    {"category": "code/backend", "project": "微服务架构", "stack": "Go + gRPC"},
    {"category": "code/backend", "project": "实时通讯系统", "stack": "WebSocket + Redis"},
    {"category": "code/backend", "project": "任务调度系统", "stack": "Python + Celery"},
    
    # 数据科学
    {"category": "code/data", "project": "推荐系统", "stack": "PyTorch + FastAPI"},
    {"category": "code/data", "project": "自然语言处理", "stack": "Transformers + BERT"},
    {"category": "code/data", "project": "计算机视觉", "stack": "OpenCV + YOLO"},
    
    # DevOps
    {"category": "code/devops", "project": "CI/CD流水线", "stack": "GitHub Actions + Docker"},
    {"category": "code/devops", "project": "监控告警系统", "stack": "Prometheus + Grafana"},
    {"category": "code/devops", "project": "基础设施即代码", "stack": "Terraform + AWS"},
    
    # 移动开发
    {"category": "code/mobile", "project": "跨平台APP", "stack": "Flutter + Firebase"},
    {"category": "code/mobile", "project": "健身追踪应用", "stack": "React Native"},
]

# 研究助手 (20%)
RESEARCH_TASKS = [
    {"category": "research/ai", "topic": "大语言模型研究综述", "type": "survey"},
    {"category": "research/ai", "topic": "强化学习最新进展", "type": "review"},
    {"category": "research/ai", "topic": "多模态学习方法", "type": "analysis"},
    
    {"category": "research/science", "topic": "量子霸权实验", "type": "report"},
    {"category": "research/science", "topic": "核聚变能源进展", "type": "overview"},
    {"category": "research/science", "topic": "太空探索计划", "type": "summary"},
    
    {"category": "research/social", "topic": "远程工作趋势", "type": "study"},
    {"category": "research/social", "topic": "教育技术革新", "type": "review"},
    {"category": "research/social", "topic": "数字隐私保护", "type": "analysis"},
]

# 教育内容 (15%)
EDUCATION_TASKS = [
    # 编程教程
    {"category": "education/programming", "topic": "Python从入门到精通", "level": "beginner"},
    {"category": "education/programming", "topic": "数据结构与算法", "level": "intermediate"},
    {"category": "education/programming", "topic": "系统设计面试", "level": "advanced"},
    {"category": "education/programming", "topic": "机器学习实战", "level": "intermediate"},
    
    # 学科教育
    {"category": "education/math", "topic": "线性代数精讲", "level": "undergraduate"},
    {"category": "education/math", "topic": "概率论与数理统计", "level": "undergraduate"},
    {"category": "education/physics", "topic": "量子力学入门", "level": "undergraduate"},
    
    # 语言学习
    {"category": "education/language", "topic": "商务英语写作", "level": "intermediate"},
    {"category": "education/language", "topic": "学术论文写作", "level": "advanced"},
    
    # 职业技能
    {"category": "education/career", "topic": "产品经理指南", "level": "professional"},
    {"category": "education/career", "topic": "数据分析师技能", "level": "professional"},
]

# 创意写作 (10%)
CREATIVE_TASKS = [
    # 小说
    {"category": "creative/novel", "genre": "科幻", "theme": "时间旅行"},
    {"category": "creative/novel", "genre": "奇幻", "theme": "魔法世界"},
    {"category": "creative/novel", "genre": "悬疑", "theme": "密室推理"},
    {"category": "creative/novel", "genre": "历史", "theme": "三国演义新编"},
    
    # 剧本
    {"category": "creative/script", "genre": "科幻电影", "theme": "AI觉醒"},
    {"category": "creative/script", "genre": "都市剧", "theme": "创业故事"},
    
    # 游戏
    {"category": "creative/game", "genre": "RPG", "theme": "开放世界"},
    {"category": "creative/game", "genre": "解谜", "theme": "时间循环"},
    
    # 诗歌
    {"category": "creative/poetry", "genre": "现代诗", "theme": "数字时代"},
    {"category": "creative/poetry", "genre": "古体诗", "theme": "山水田园"},
]

ALL_TASKS = KNOWLEDGE_TASKS + CODE_TASKS + RESEARCH_TASKS + EDUCATION_TASKS + CREATIVE_TASKS

# ============ 工具函数 ============

def log(msg: str):
    """写日志"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def load_stats() -> dict:
    if STATS_FILE.exists():
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return {
        "total_tokens": 0,
        "total_calls": 0,
        "total_input": 0,
        "total_output": 0,
        "content_generated": 0,
        "start_time": None,
        "last_update": None,
        "errors": 0,
        "by_category": {},
    }

def save_stats(stats: dict):
    stats["last_update"] = datetime.now().isoformat()
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

def save_content(task: dict, content: str, tokens_used: int):
    """保存生成的内容"""
    category = task.get("category", "other")
    output_dir = OUTPUT_DIR / category
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    topic = task.get("topic", task.get("project", "unknown"))
    safe_name = "".join(c for c in topic[:30] if c.isalnum() or c in "._- ").strip()
    filename = f"{timestamp}_{safe_name}.md"
    
    filepath = output_dir / filename
    
    # 生成元数据
    metadata = f"""---
category: {category}
topic: {topic}
generated: {datetime.now().isoformat()}
tokens_used: {tokens_used}
model: {MODEL}
---

# {topic}

"""
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(metadata + content)
    
    return filepath

def generate_prompt(task: dict) -> str:
    """根据任务生成详细 prompt"""
    category = task.get("category", "")
    topic = task.get("topic", task.get("project", ""))
    
    if "knowledge" in category:
        return f"""请写一篇关于"{topic}"的深度文章。

要求：
1. 文章长度：至少 6000 字
2. 完整结构：引言、多个章节、结论
3. 详细内容：原理、案例、数据、图表说明
4. 专业深度：包含技术细节和最新进展
5. 实用价值：对读者有实际帮助
6. 多角度分析：技术、应用、趋势、挑战

请开始写作："""
    
    elif "code" in category:
        stack = task.get("stack", "Python")
        project = task.get("project", topic)
        return f"""请用 {stack} 实现一个完整的{project}项目。

要求：
1. 完整项目结构（目录、文件、配置）
2. 核心功能实现（不是示例，是真实可用的代码）
3. 详细注释和文档
4. 错误处理和边界情况
5. 单元测试
6. 部署指南
7. 性能优化建议
8. 安全最佳实践

请提供完整代码和文档："""
    
    elif "research" in category:
        rtype = task.get("type", "survey")
        return f"""请写一篇关于"{topic}"的{rtype}。

要求：
1. 文献综述：引用 20+ 篇相关研究
2. 方法论：分析研究方法和数据来源
3. 发现总结：关键发现和趋势
4. 研究空白：指出未解决的问题
5. 未来方向：提出研究建议
6. 至少 8000 字

请开始撰写："""
    
    elif "education" in category:
        level = task.get("level", "beginner")
        return f"""请写一个"{topic}"的完整教程，难度：{level}

要求：
1. 学习目标明确
2. 从基础到进阶的完整路径
3. 大量示例和练习
4. 常见错误及解决方案
5. 最佳实践
6. 扩展资源
7. 至少 8000 字

请开始写教程："""
    
    elif "creative" in category:
        genre = task.get("genre", "")
        theme = task.get("theme", "")
        return f"""请创作一个{genre}作品，主题：{theme}

要求：
1. 完整的故事结构
2. 丰富的人物塑造
3. 详细的场景描写
4. 引人入胜的情节
5. 独特的创意和视角
6. 至少 8000 字

请开始创作："""
    
    else:
        return f"请详细讨论{topic}，至少 6000 字。"

# ============ API 调用 ============

async def call_mimo(session: aiohttp.ClientSession, task: dict, stats: dict) -> dict:
    """调用 MiMo API"""
    prompt = generate_prompt(task)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一个专业的AI助手，擅长撰写高质量、有深度的内容。请确保输出结构清晰、内容详实。"},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": MAX_OUTPUT_TOKENS,
        "temperature": 0.8,
        "stream": False,
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with session.post(
                f"{API_BASE}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=180),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    usage = data.get("usage", {})
                    input_tokens = usage.get("prompt_tokens", 0)
                    output_tokens = usage.get("completion_tokens", 0)
                    total = input_tokens + output_tokens
                    
                    # 提取内容
                    content = data["choices"][0]["message"]["content"]
                    
                    # 保存内容
                    filepath = save_content(task, content, total)
                    
                    # 更新统计
                    stats["total_tokens"] += total
                    stats["total_calls"] += 1
                    stats["total_input"] += input_tokens
                    stats["total_output"] += output_tokens
                    stats["content_generated"] += 1
                    
                    # 分类统计
                    category = task.get("category", "other")
                    if category not in stats["by_category"]:
                        stats["by_category"][category] = {"calls": 0, "tokens": 0}
                    stats["by_category"][category]["calls"] += 1
                    stats["by_category"][category]["tokens"] += total
                    
                    return {
                        "success": True,
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": total,
                        "filepath": str(filepath),
                        "category": category,
                    }
                elif resp.status == 429:
                    retry_after = int(resp.headers.get("Retry-After", 5))
                    log(f"Rate limit, waiting {retry_after}s...")
                    await asyncio.sleep(retry_after)
                    continue
                else:
                    error_text = await resp.text()
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    stats["errors"] += 1
                    return {"success": False, "error": f"HTTP {resp.status}: {error_text[:200]}"}
        
        except asyncio.TimeoutError:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            stats["errors"] += 1
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            stats["errors"] += 1
            return {"success": False, "error": str(e)[:200]}
    
    stats["errors"] += 1
    return {"success": False, "error": "Max retries exceeded"}

async def worker(worker_id: int, session: aiohttp.ClientSession, stats: dict, stop_event: asyncio.Event):
    """Worker 协程"""
    while not stop_event.is_set():
        task = random.choice(ALL_TASKS)
        result = await call_mimo(session, task, stats)
        
        if result["success"]:
            log(f"[W{worker_id:03d}] OK | {result['category']} | +{result['total']:,} tokens | {Path(result['filepath']).name}")
        else:
            log(f"[W{worker_id:03d}] ERR | {result['error']}")
            await asyncio.sleep(1)

async def stats_reporter(stats: dict, stop_event: asyncio.Event):
    """统计报告协程"""
    while not stop_event.is_set():
        await asyncio.sleep(300)  # 每5分钟报告一次
        
        elapsed = time.time() - stats.get("_start", time.time())
        hours = elapsed / 3600
        rate = stats["total_tokens"] / hours if hours > 0 else 0
        remaining = (TOTAL_TARGET - stats["total_tokens"]) / rate if rate > 0 else float('inf')
        
        log("=" * 60)
        log("📊 生产统计")
        log(f"  总 tokens: {stats['total_tokens']:,} / {TOTAL_TARGET:,} ({stats['total_tokens']/TOTAL_TARGET*100:.2f}%)")
        log(f"  内容生成: {stats['content_generated']} 篇")
        log(f"  速率: {rate/1e6:.2f}M tokens/h")
        log(f"  运行时间: {hours:.2f} 小时")
        log(f"  预计剩余: {remaining:.2f} 小时 ({remaining/24:.1f} 天)")
        log(f"  错误: {stats['errors']}")
        log("=" * 60)
        
        save_stats(stats)

async def main():
    """主函数"""
    if not API_KEY:
        print("错误: 未设置 CUSTOM_API_KEY")
        sys.exit(1)
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    log("=" * 60)
    log("🏭 MiMo Content Factory 启动")
    log(f"目标: {TOTAL_TARGET/1e9:.0f}B tokens, {DAYS} 天")
    log(f"并发: {CONCURRENCY}")
    log(f"输出: {OUTPUT_DIR}")
    log("=" * 60)
    
    stats = load_stats()
    stats["_start"] = time.time()
    if not stats["start_time"]:
        stats["start_time"] = datetime.now().isoformat()
    
    stop_event = asyncio.Event()
    
    async with aiohttp.ClientSession() as session:
        workers = [
            asyncio.create_task(worker(i, session, stats, stop_event))
            for i in range(CONCURRENCY)
        ]
        
        reporter = asyncio.create_task(stats_reporter(stats, stop_event))
        
        try:
            while stats["total_tokens"] < TOTAL_TARGET:
                await asyncio.sleep(1)
                
                if stats["total_tokens"] >= TOTAL_TARGET:
                    log("🎉 目标达成！")
                    break
        
        except KeyboardInterrupt:
            log("收到中断信号，正在停止...")
        
        finally:
            stop_event.set()
            for w in workers:
                w.cancel()
            reporter.cancel()
            await asyncio.gather(*workers, reporter, return_exceptions=True)
            
            save_stats(stats)
            
            log("=" * 60)
            log("📋 最终统计")
            log(f"  总 tokens: {stats['total_tokens']:,}")
            log(f"  内容生成: {stats['content_generated']} 篇")
            log(f"  错误: {stats['errors']}")
            log("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
