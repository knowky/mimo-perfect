#!/usr/bin/env python3
"""
MiMo 高质量内容生产系统
- 少而精，每篇都是精品
- 调动所有 skill
- 质量迭代保证
- 不限算力，最大并发
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
API_KEY = ***"CUSTOM_API_KEY", "")
MODEL = "mimo-v2.5-pro"

CONCURRENCY = 100           # 最大并发
QUALITY_ITERATIONS = 3      # 每篇内容迭代轮数
MAX_OUTPUT_TOKENS = 8000    # 每次输出 tokens
TOTAL_TARGET = 38_000_000_000
DAYS = 6

OUTPUT_DIR = Path(__file__).parent / "quality_output"
STATS_FILE = Path(__file__).parent / "quality_stats.json"
LOG_FILE = Path(__file__).parent / "quality_log.txt"

# ============ Skill 系统提示 ============

SKILL_PROMPTS = {
    "thinking": """你是一个深度思考专家。在生成内容时：
- 运用心理学原理分析问题
- 使用批判性思维审视观点
- 提供多角度的见解
- 揭示表面现象下的深层逻辑""",
    
    "research": """你是一个严谨的研究员。在生成内容时：
- 引用可靠的数据来源
- 使用科学的研究方法
- 提供可验证的证据
- 保持客观中立的立场""",
    
    "creative": """你是一个富有创造力的作家。在生成内容时：
- 运用生动的描写和比喻
- 构建引人入胜的故事
- 塑造鲜明的人物形象
- 创造独特的世界观""",
    
    "technical": """你是一个技术专家。在生成内容时：
- 使用准确的技术术语
- 提供可运行的代码示例
- 解释底层原理和机制
- 给出最佳实践建议""",
    
    "educational": """你是一个优秀的教育者。在生成内容时：
- 循序渐进地讲解概念
- 使用通俗易懂的比喻
- 提供丰富的练习题
- 关注学习者的认知规律""",
}

# ============ 高质量任务模板 ============

TASKS = [
    # 深度研究报告 (1000 篇)
    {
        "type": "research_report",
        "category": "reports/tech",
        "topics": [
            "量子计算商业化路径与挑战",
            "大语言模型的能力边界与未来演进",
            "脑机接口技术现状与伦理思考",
            "核聚变能源的工程化突破",
            "合成生物学的产业应用",
            "太空经济的商业模式创新",
            "Web3.0 的技术栈与应用前景",
            "自动驾驶 L5 的技术瓶颈",
            "通用人工智能的实现路径",
            "数字孪生在工业中的应用",
        ],
        "skill": "research",
        "depth": "万字深度报告",
    },
    {
        "type": "research_report",
        "category": "reports/business",
        "topics": [
            "全球供应链重构趋势分析",
            "新能源汽车产业链深度研究",
            "半导体产业格局与国产替代",
            "跨境电商的下一个增长点",
            "SaaS 行业的商业模式演进",
            "银发经济的市场机会",
            "碳中和带来的产业变革",
            "元宇宙的商业落地路径",
            "AI 创业的机会与风险",
            "生物医药的投资逻辑",
        ],
        "skill": "research",
        "depth": "行业深度分析",
    },
    {
        "type": "research_report",
        "category": "reports/society",
        "topics": [
            "远程办公对社会结构的影响",
            "Z 世代的消费行为研究",
            "教育公平的技术解决方案",
            "老龄化社会的应对策略",
            "数字隐私保护的法律框架",
            "社交媒体对心理健康的影响",
            "城市化进程中的空间规划",
            "气候变化的社会适应策略",
            "AI 就业替代与技能转型",
            "全球化的退潮与重构",
        ],
        "skill": "thinking",
        "depth": "社会研究报告",
    },
    
    # 完整技术项目 (200 个)
    {
        "type": "tech_project",
        "category": "code/fullstack",
        "projects": [
            {"name": "分布式电商系统", "stack": "Go + gRPC + PostgreSQL + Redis"},
            {"name": "实时协作编辑器", "stack": "TypeScript + WebSocket + CRDT"},
            {"name": "智能推荐引擎", "stack": "Python + PyTorch + FastAPI"},
            {"name": "微服务网关", "stack": "Rust + Tokio + Prometheus"},
            {"name": "区块链浏览器", "stack": "React + Node.js + MongoDB"},
            {"name": "视频流媒体平台", "stack": "FFmpeg + HLS + CDN"},
            {"name": "即时通讯系统", "stack": "Erlang + WebSocket + PostgreSQL"},
            {"name": "任务调度平台", "stack": "Java + Spring Boot + Kafka"},
            {"name": "API 管理平台", "stack": "Go + OpenAPI + Rate Limiting"},
            {"name": "监控告警系统", "stack": "Prometheus + Grafana + AlertManager"},
        ],
        "skill": "technical",
        "depth": "完整可运行项目",
    },
    
    # 学术级教程 (800 篇)
    {
        "type": "academic_tutorial",
        "category": "tutorials/programming",
        "topics": [
            "分布式系统设计：从理论到实践",
            "编译原理：手写一个编程语言",
            "操作系统内核：从零实现",
            "数据库内核：存储引擎设计",
            "网络协议栈：TCP/IP 实现",
            "机器学习算法：从数学到代码",
            "深度学习框架：手写 PyTorch",
            "密码学：从古典到量子",
            "并发编程：从原理到模式",
            "系统性能优化：全栈方法",
        ],
        "skill": "educational",
        "depth": "教材级教程",
    },
    {
        "type": "academic_tutorial",
        "category": "tutorials/math",
        "topics": [
            "线性代数的几何直觉",
            "概率论的贝叶斯视角",
            "微积分的物理应用",
            "离散数学的计算机应用",
            "最优化理论与算法",
            "信息论基础",
            "随机过程与金融模型",
            "图论与网络科学",
            "抽象代数入门",
            "实分析基础",
        ],
        "skill": "educational",
        "depth": "数学教材",
    },
    
    # 创意作品 (500 部)
    {
        "type": "creative_work",
        "category": "creative/scifi",
        "stories": [
            {"title": "量子纠缠：跨越时空的对话", "theme": "量子通讯"},
            {"title": "最后一个程序员", "theme": "AI 取代人类"},
            {"title": "记忆交易市场", "theme": "记忆移植"},
            {"title": "数字永生：意识上传", "theme": "意识上传"},
            {"title": "时间回溯者", "theme": "时间旅行悖论"},
            {"title": "星际播种者", "theme": "太空殖民"},
            {"title": "基因黑客", "theme": "基因编辑"},
            {"title": "虚拟偶像的觉醒", "theme": "AI 意识"},
            {"title": "暗物质信使", "theme": "宇宙探索"},
            {"title": "意识黑客", "theme": "脑机接口"},
        ],
        "skill": "creative",
        "depth": "中篇小说",
    },
    {
        "type": "creative_work",
        "category": "creative/fantasy",
        "stories": [
            {"title": "元素编年史", "theme": "魔法体系"},
            {"title": "龙与最后的程序员", "theme": "科技与魔法"},
            {"title": "时间之塔", "theme": "时间魔法"},
            {"title": "梦境行者", "theme": "梦境世界"},
            {"title": "符文语言学", "theme": "语言魔法"},
            {"title": "灵魂锻造师", "theme": "灵魂魔法"},
            {"title": "星辰之子", "theme": "宇宙神话"},
            {"title": "影子议会", "theme": "暗影魔法"},
            {"title": "命运编织者", "theme": "命运魔法"},
            {"title": "元素之战", "theme": "元素冲突"},
        ],
        "skill": "creative",
        "depth": "奇幻小说",
    },
    
    # 行业分析 (500 篇)
    {
        "type": "industry_analysis",
        "category": "analysis/industries",
        "topics": [
            "人工智能产业链全景图",
            "新能源汽车竞争格局",
            "半导体国产化进程",
            "生物医药创新趋势",
            "云计算市场分析",
            "智能制造转型路径",
            "金融科技监管与发展",
            "教育科技商业模式",
            "文娱产业数字化",
            "农业现代化路径",
        ],
        "skill": "research",
        "depth": "行业深度分析",
    },
]

# ============ 工具函数 ============

def log(msg: str):
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
        "quality_iterations": 0,
        "start_time": None,
        "last_update": None,
        "errors": 0,
        "by_type": {},
    }

def save_stats(stats: dict):
    stats["last_update"] = datetime.now().isoformat()
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

def save_content(task: dict, content: str, iteration: int, tokens_used: int):
    """保存高质量内容"""
    category = task.get("category", "other")
    output_dir = OUTPUT_DIR / category
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 获取标题
    if "topics" in task:
        title = random.choice(task["topics"])
    elif "projects" in task:
        proj = random.choice(task["projects"])
        title = proj["name"]
    elif "stories" in task:
        story = random.choice(task["stories"])
        title = story["title"]
    else:
        title = "unknown"
    
    safe_name = "".join(c for c in title[:30] if c.isalnum() or c in "._- ").strip()
    filename = f"{timestamp}_{safe_name}_v{iteration}.md"
    filepath = output_dir / filename
    
    skill = task.get("skill", "general")
    depth = task.get("depth", "文章")
    
    metadata = f"""---
type: {task['type']}
category: {category}
title: {title}
skill: {skill}
depth: {depth}
iteration: {iteration}
generated: {datetime.now().isoformat()}
tokens_used: {tokens_used}
model: {MODEL}
quality_level: {'初稿' if iteration == 1 else '优化稿' if iteration == 2 else '终稿'}
---

# {title}

"""
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(metadata + content)
    
    return filepath

def generate_prompt(task: dict, iteration: int, prev_content: str = "") -> str:
    """生成高质量 prompt，结合 skill"""
    task_type = task["type"]
    skill = task.get("skill", "general")
    depth = task.get("depth", "文章")
    system_prompt = SKILL_PROMPTS.get(skill, "")
    
    # 获取具体主题
    if "topics" in task:
        topic = random.choice(task["topics"])
    elif "projects" in task:
        proj = random.choice(task["projects"])
        topic = f"{proj['name']} ({proj['stack']})"
    elif "stories" in task:
        story = random.choice(task["stories"])
        topic = f"{story['title']} - {story['theme']}"
    else:
        topic = "未知主题"
    
    # 根据迭代轮次调整 prompt
    if iteration == 1:
        # 初稿：完整生成
        if task_type == "research_report":
            return f"""{system_prompt}

请撰写一份关于"{topic}"的{depth}。

要求：
1. 字数：至少 10000 字
2. 结构：执行摘要、背景分析、核心内容（至少5个章节）、数据支撑、结论与建议
3. 深度：包含专业分析、数据引用、案例研究
4. 视角：多角度分析（技术、市场、政策、社会影响）
5. 可操作性：提供具体建议和行动方案

请开始撰写完整报告："""
        
        elif task_type == "tech_project":
            return f"""{system_prompt}

请实现一个完整的"{topic}"项目。

要求：
1. 项目结构：完整的目录结构和文件组织
2. 核心代码：所有核心功能的实现（不是示例，是真实可用的代码）
3. 详细注释：每个函数、类、模块都有详细注释
4. 错误处理：完整的异常处理和边界情况
5. 测试用例：单元测试和集成测试
6. 文档：README、API 文档、部署指南
7. 最佳实践：遵循语言和框架的最佳实践

请提供完整项目代码："""
        
        elif task_type == "academic_tutorial":
            return f"""{system_prompt}

请撰写一个"{topic}"的{depth}。

要求：
1. 字数：至少 10000 字
2. 结构：学习目标、前置知识、核心内容（至少8章）、练习题、参考文献
3. 深度：从原理到实践，深入浅出
4. 示例：大量代码示例和图示说明
5. 练习：每章配套练习题和答案
6. 扩展：提供进一步学习的资源

请开始撰写教程："""
        
        elif task_type == "creative_work":
            return f"""{system_prompt}

请创作"{topic}"。

要求：
1. 字数：至少 10000 字
2. 结构：完整的故事结构（开端、发展、高潮、结局）
3. 人物：至少 5 个主要角色，详细的人物设定
4. 世界观：完整的世界观设定
5. 细节：丰富的场景描写和细节刻画
6. 主题：深刻的主题思考

请开始创作："""
        
        elif task_type == "industry_analysis":
            return f"""{system_prompt}

请撰写"{topic}"的{depth}。

要求：
1. 字数：至少 8000 字
2. 结构：行业概述、市场分析、竞争格局、趋势预测、投资建议
3. 数据：引用权威数据来源
4. 案例：至少 5 个详细案例
5. 图表：提供数据图表说明
6. 建议：提供可操作的建议

请开始撰写分析："""
    
    elif iteration == 2:
        # 第二轮：深度扩展
        return f"""{system_prompt}

以下是初稿内容，请进行深度扩展和优化：

{prev_content[:3000]}...

请进行以下优化：
1. 补充更多细节和案例
2. 深化分析和论证
3. 增加数据支撑
4. 完善逻辑结构
5. 提升语言质量
6. 增加实用价值

请输出优化后的完整内容："""
    
    elif iteration == 3:
        # 第三轮：质量打磨
        return f"""{system_prompt}

以下是优化稿内容，请进行最终的质量打磨：

{prev_content[:3000]}...

请进行以下打磨：
1. 语言润色：提升文字表达质量
2. 逻辑优化：确保论证严密
3. 格式美化：优化排版和格式
4. 错误修正：修正任何错误
5. 价值提升：增加可操作性和实用性

请输出最终精品内容："""
    
    return f"请详细讨论{topic}，至少 10000 字。"

# ============ API 调用 ============

async def call_mimo(session: aiohttp.ClientSession, prompt: str, stats: dict) -> dict:
    """调用 MiMo API"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一个顶级专家，擅长撰写高质量、有深度、有实用价值的内容。请确保输出结构清晰、内容详实、语言精炼。"},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": MAX_OUTPUT_TOKENS,
        "temperature": 0.7,
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
                    
                    content = data["choices"][0]["message"]["content"]
                    
                    stats["total_tokens"] += total
                    stats["total_calls"] += 1
                    stats["total_input"] += input_tokens
                    stats["total_output"] += output_tokens
                    
                    return {
                        "success": True,
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": total,
                        "content": content,
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

async def produce_content(worker_id: int, session: aiohttp.ClientSession, task: dict, stats: dict):
    """生产一篇高质量内容（多轮迭代）"""
    task_type = task["type"]
    
    log(f"[W{worker_id:03d}] 开始生产: {task_type}")
    
    prev_content = ""
    total_tokens = 0
    
    for iteration in range(1, QUALITY_ITERATIONS + 1):
        prompt = generate_prompt(task, iteration, prev_content)
        result = await call_mimo(session, prompt, stats)
        
        if not result["success"]:
            log(f"[W{worker_id:03d}] 迭代 {iteration} 失败: {result['error']}")
            return
        
        prev_content = result["content"]
        total_tokens += result["total"]
        stats["quality_iterations"] += 1
        
        log(f"[W{worker_id:03d}] 迭代 {iteration}/{QUALITY_ITERATIONS} 完成 | +{result['total']:,} tokens")
    
    # 保存最终内容
    filepath = save_content(task, prev_content, QUALITY_ITERATIONS, total_tokens)
    
    stats["content_generated"] += 1
    
    # 分类统计
    if task_type not in stats["by_type"]:
        stats["by_type"][task_type] = {"count": 0, "tokens": 0}
    stats["by_type"][task_type]["count"] += 1
    stats["by_type"][task_type]["tokens"] += total_tokens
    
    log(f"[W{worker_id:03d}] ✅ 完成: {filepath.name} | 总计 {total_tokens:,} tokens")

async def worker(worker_id: int, session: aiohttp.ClientSession, stats: dict, stop_event: asyncio.Event):
    """Worker 协程"""
    while not stop_event.is_set():
        task = random.choice(TASKS)
        await produce_content(worker_id, session, task, stats)
        
        # 短暂休息，避免过热
        await asyncio.sleep(1)

async def stats_reporter(stats: dict, stop_event: asyncio.Event):
    """统计报告协程"""
    while not stop_event.is_set():
        await asyncio.sleep(300)  # 每5分钟报告
        
        elapsed = time.time() - stats.get("_start", time.time())
        hours = elapsed / 3600
        rate = stats["total_tokens"] / hours if hours > 0 else 0
        remaining = (TOTAL_TARGET - stats["total_tokens"]) / rate if rate > 0 else float('inf')
        
        log("=" * 70)
        log("📊 高质量生产统计")
        log(f"  总 tokens: {stats['total_tokens']:,} / {TOTAL_TARGET:,} ({stats['total_tokens']/TOTAL_TARGET*100:.2f}%)")
        log(f"  内容生成: {stats['content_generated']} 篇")
        log(f"  质量迭代: {stats['quality_iterations']} 次")
        log(f"  速率: {rate/1e6:.2f}M tokens/h")
        log(f"  运行时间: {hours:.2f} 小时")
        log(f"  预计剩余: {remaining:.2f} 小时 ({remaining/24:.1f} 天)")
        log(f"  错误: {stats['errors']}")
        
        if stats["by_type"]:
            log("  按类型:")
            for t, data in stats["by_type"].items():
                log(f"    {t}: {data['count']} 篇, {data['tokens']/1e6:.1f}M tokens")
        
        log("=" * 70)
        
        save_stats(stats)

async def main():
    if not API_KEY:
        ***"错误: 未设置 CUSTOM_API_KEY")
        sys.exit(1)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    log("=" * 70)
    log("🏭 MiMo 高质量内容生产系统")
    log(f"目标: {TOTAL_TARGET/1e9:.0f}B tokens, {DAYS} 天")
    log(f"并发: {CONCURRENCY}")
    log(f"质量迭代: {QUALITY_ITERATIONS} 轮")
    log(f"输出: {OUTPUT_DIR}")
    log("=" * 70)
    
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
            
            log("=" * 70)
            log("📋 最终统计")
            log(f"  总 tokens: {stats['total_tokens']:,}")
            log(f"  内容生成: {stats['content_generated']} 篇")
            log(f"  质量迭代: {stats['quality_iterations']} 次")
            log(f"  错误: {stats['errors']}")
            log("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
