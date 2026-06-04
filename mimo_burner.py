#!/usr/bin/env python3
"""
MiMo Token Burner - 高效消耗 MiMo 模型 tokens
目标: 6天内用完 38,000,000,000 tokens
方案: 50-100 并发直接调用 API
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

# 并发配置
CONCURRENCY = 50  # 并发数，可调整 20-200
MAX_OUTPUT_TOKENS = 8000  # 每次输出 tokens（接近 maxTokens=8192）
MAX_INPUT_TOKENS = 5000   # 每次输入 tokens（最小化以提高效率）

# 目标
TOTAL_TARGET = 38_000_000_000  # 38B tokens
DAYS = 6

# 统计文件
STATS_FILE = Path(__file__).parent / "burn_stats.json"
LOG_FILE = Path(__file__).parent / "burn_log.txt"

# ============ 任务模板 ============
TASKS = [
    # 文章生成
    {"type": "article", "topic": "量子计算的未来发展", "lang": "zh"},
    {"type": "article", "topic": "人工智能在医疗领域的应用", "lang": "zh"},
    {"type": "article", "topic": "区块链技术的演进", "lang": "zh"},
    {"type": "article", "topic": "太空探索的下一个里程碑", "lang": "zh"},
    {"type": "article", "topic": "可再生能源的突破", "lang": "zh"},
    {"type": "article", "topic": "The Future of Quantum Computing", "lang": "en"},
    {"type": "article", "topic": "AI Applications in Healthcare", "lang": "en"},
    {"type": "article", "topic": "Blockchain Evolution", "lang": "en"},
    
    # 代码生成
    {"type": "code", "lang": "python", "task": "Web scraper with async"},
    {"type": "code", "lang": "python", "task": "Machine learning pipeline"},
    {"type": "code", "lang": "python", "task": "API server with FastAPI"},
    {"type": "code", "lang": "javascript", "task": "React component library"},
    {"type": "code", "lang": "javascript", "task": "Node.js microservice"},
    {"type": "code", "lang": "rust", "task": "CLI tool with error handling"},
    {"type": "code", "lang": "go", "task": "Concurrent web crawler"},
    {"type": "code", "lang": "typescript", "task": "Type-safe API client"},
    
    # 翻译任务
    {"type": "translate", "from": "en", "to": "zh", "text": "Technical documentation"},
    {"type": "translate", "from": "zh", "to": "en", "text": "学术论文摘要"},
    
    # 分析任务
    {"type": "analysis", "topic": "全球气候变化数据"},
    {"type": "analysis", "topic": "科技行业市场趋势"},
    {"type": "analysis", "topic": "教育体系比较研究"},
    
    # 创意写作
    {"type": "creative", "genre": "科幻小说", "prompt": "时间旅行悖论"},
    {"type": "creative", "genre": "fantasy", "prompt": "Magic system design"},
    {"type": "creative", "genre": "推理小说", "prompt": "密室杀人案"},
    
    # 问答对生成
    {"type": "qa", "domain": "计算机科学", "count": 50},
    {"type": "qa", "domain": "数学", "count": 50},
    {"type": "qa", "domain": "物理", "count": 50},
    
    # 教程生成
    {"type": "tutorial", "topic": "Python高级编程", "level": "advanced"},
    {"type": "tutorial", "topic": "系统设计面试", "level": "intermediate"},
    {"type": "tutorial", "topic": "机器学习入门", "level": "beginner"},
]

# ============ 工具函数 ============

def log(msg: str):
    """写日志"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def load_stats() -> dict:
    """加载统计"""
    if STATS_FILE.exists():
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return {
        "total_tokens": 0,
        "total_calls": 0,
        "total_input": 0,
        "total_output": 0,
        "start_time": None,
        "last_update": None,
        "errors": 0,
    }

def save_stats(stats: dict):
    """保存统计"""
    stats["last_update"] = datetime.now().isoformat()
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)

def generate_prompt(task: dict) -> str:
    """根据任务生成 prompt"""
    t = task["type"]
    
    if t == "article":
        if task["lang"] == "zh":
            return f"""请写一篇关于"{task['topic']}"的深度文章。

要求：
1. 文章长度：至少 6000 字
2. 结构：引言、多个章节、结论
3. 内容：详细分析、案例、数据支撑
4. 语言：专业但易懂
5. 包含：历史背景、现状分析、未来展望

请开始写作："""
        else:
            return f"""Write a comprehensive article about "{task['topic']}".

Requirements:
1. Length: at least 4000 words
2. Structure: introduction, multiple sections, conclusion
3. Content: detailed analysis, case studies, data
4. Language: professional but accessible
5. Include: history, current state, future outlook

Begin writing:"""
    
    elif t == "code":
        return f"""请用 {task['lang']} 实现以下项目：{task['task']}

要求：
1. 完整的项目结构
2. 详细的注释
3. 错误处理
4. 单元测试
5. 使用说明文档
6. 性能优化建议
7. 最佳实践遵循

请提供完整代码："""
    
    elif t == "translate":
        return f"""请将以下{task['from']}文本翻译成{task['to']}，并提供详细注释：

原文主题：{task['text']}

要求：
1. 准确翻译
2. 保持原意
3. 添加文化背景注释
4. 术语对照表
5. 翻译技巧说明

请开始翻译（至少 5000 字）："""
    
    elif t == "analysis":
        return f"""请对"{task['topic']}"进行深度分析。

要求：
1. 数据收集方法
2. 统计分析
3. 趋势预测
4. 可视化建议
5. 洞察与结论
6. 决策建议

请提供详细分析报告（至少 6000 字）："""
    
    elif t == "creative":
        return f"""请创作一个{task['genre']}故事，主题：{task['prompt']}

要求：
1. 完整的故事结构
2. 丰富的人物塑造
3. 详细的场景描写
4. 引人入胜的情节
5. 至少 8000 字

请开始创作："""
    
    elif t == "qa":
        return f"""请生成关于"{task['domain']}"领域的 {task['count']} 个问答对。

要求：
1. 难度：从基础到高级
2. 覆盖面广
3. 详细解答
4. 包含代码示例（如适用）
5. 扩展阅读建议

请开始生成："""
    
    elif t == "tutorial":
        return f"""请写一个{task['topic']}的完整教程，难度：{task['level']}

要求：
1. 从基础到进阶
2. 大量代码示例
3. 练习题
4. 常见错误及解决方案
5. 最佳实践
6. 至少 8000 字

请开始写教程："""
    
    else:
        return "请详细讨论人工智能的未来发展趋势，至少 5000 字。"

# ============ API 调用 ============

async def call_mimo(session: aiohttp.ClientSession, task: dict, stats: dict) -> dict:
    """调用 MiMo API，带重试机制"""
    prompt = generate_prompt(task)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一个专业的AI助手，请提供详细、准确、有深度的回答。"},
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
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    usage = data.get("usage", {})
                    input_tokens = usage.get("prompt_tokens", 0)
                    output_tokens = usage.get("completion_tokens", 0)
                    total = input_tokens + output_tokens
                    
                    # 更新统计
                    stats["total_tokens"] += total
                    stats["total_calls"] += 1
                    stats["total_input"] += input_tokens
                    stats["total_output"] += output_tokens
                    
                    return {
                        "success": True,
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": total,
                    }
                elif resp.status == 429:  # Rate limit
                    retry_after = int(resp.headers.get("Retry-After", 5))
                    log(f"Rate limit hit, waiting {retry_after}s...")
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
        task = random.choice(TASKS)
        result = await call_mimo(session, task, stats)
        
        if result["success"]:
            log(f"[Worker {worker_id:03d}] OK | +{result['total']:,} tokens (in:{result['input']:,} out:{result['output']:,})")
        else:
            log(f"[Worker {worker_id:03d}] ERR | {result['error']}")
            await asyncio.sleep(1)  # 错误后短暂等待

async def stats_reporter(stats: dict, stop_event: asyncio.Event):
    """统计报告协程"""
    while not stop_event.is_set():
        await asyncio.sleep(60)  # 每分钟报告一次
        
        elapsed = time.time() - stats.get("_start", time.time())
        hours = elapsed / 3600
        rate = stats["total_tokens"] / hours if hours > 0 else 0
        remaining = (TOTAL_TARGET - stats["total_tokens"]) / rate if rate > 0 else float('inf')
        
        log(f"=== 统计 ===")
        log(f"  总 tokens: {stats['total_tokens']:,} / {TOTAL_TARGET:,} ({stats['total_tokens']/TOTAL_TARGET*100:.2f}%)")
        log(f"  调用次数: {stats['total_calls']:,}")
        log(f"  输入 tokens: {stats['total_input']:,}")
        log(f"  输出 tokens: {stats['total_output']:,}")
        log(f"  错误次数: {stats['errors']:,}")
        log(f"  速率: {rate/1e6:.2f}M tokens/h")
        log(f"  运行时间: {hours:.2f} 小时")
        log(f"  预计剩余: {remaining:.2f} 小时 ({remaining/24:.1f} 天)")
        
        save_stats(stats)

async def main():
    """主函数"""
    if not API_KEY:
        print("错误: 未设置 CUSTOM_API_KEY 环境变量")
        sys.exit(1)
    
    log("=" * 60)
    log("MiMo Token Burner 启动")
    log(f"目标: {TOTAL_TARGET/1e9:.0f}B tokens, {DAYS} 天")
    log(f"并发数: {CONCURRENCY}")
    log(f"每次调用: {MAX_INPUT_TOKENS} input + {MAX_OUTPUT_TOKENS} output")
    log("=" * 60)
    
    stats = load_stats()
    stats["_start"] = time.time()
    if not stats["start_time"]:
        stats["start_time"] = datetime.now().isoformat()
    
    stop_event = asyncio.Event()
    
    async with aiohttp.ClientSession() as session:
        # 启动 workers
        workers = [
            asyncio.create_task(worker(i, session, stats, stop_event))
            for i in range(CONCURRENCY)
        ]
        
        # 启动统计报告
        reporter = asyncio.create_task(stats_reporter(stats, stop_event))
        
        try:
            # 运行直到达成目标或被中断
            while stats["total_tokens"] < TOTAL_TARGET:
                await asyncio.sleep(1)
                
                # 检查是否需要停止
                if stats["total_tokens"] >= TOTAL_TARGET:
                    log("🎉 目标达成！")
                    break
        
        except KeyboardInterrupt:
            log("收到中断信号，正在停止...")
        
        finally:
            stop_event.set()
            
            # 等待所有 worker 完成
            for w in workers:
                w.cancel()
            reporter.cancel()
            
            await asyncio.gather(*workers, reporter, return_exceptions=True)
            
            # 最终统计
            save_stats(stats)
            log("=" * 60)
            log("最终统计:")
            log(f"  总 tokens: {stats['total_tokens']:,}")
            log(f"  总调用: {stats['total_calls']:,}")
            log(f"  错误: {stats['errors']:,}")
            log("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
