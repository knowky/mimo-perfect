#!/usr/bin/env python3
"""
MiMo 完美方案 - 任务调度器
使用 OpenClaw 子 Agent 执行高质量任务
"""

import json
import asyncio
import aiohttp
import time
import random
import os
from datetime import datetime
from pathlib import Path

# ============ 配置 ============
API_BASE = "https://token-plan-cn.xiaomimimo.com/v1"
API_KEY = os.environ.get("CUSTOM_API_KEY", "")
MODEL = "mimo-v2.5-pro"

CONCURRENCY = 8  # 低并发，留出资源给ClawX
MAX_OUTPUT_TOKENS = 16000  # 适中的token量
TOTAL_TARGET = 38_000_000_000  # 38B Credits

TASKS_FILE = Path(__file__).parent / "tasks.json"
STATS_FILE = Path(__file__).parent / "perfect_stats.json"
LOG_FILE = Path(__file__).parent / "perfect_log.txt"
PROJECTS_DIR = Path(__file__).parent / "projects"

# ============ 工具函数 ============

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line.encode('utf-8', errors='replace').decode('utf-8'), flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def load_tasks() -> list:
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_stats() -> dict:
    if STATS_FILE.exists():
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return {
        "total_tokens": 0,
        "total_calls": 0,
        "completed_tasks": 0,
        "failed_tasks": 0,
        "start_time": None,
        "last_update": None,
        "errors": 0,
        "task_history": [],
    }

def save_stats(stats: dict):
    stats["last_update"] = datetime.now().isoformat()
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

# ============ 子 Agent 任务生成 ============

def generate_agent_prompt(task: dict) -> str:
    """为子 Agent 生成详细的任务 prompt"""
    task_type = task["type"]
    title = task["title"]
    description = task["description"]
    tasks_list = "\n".join(f"- {t}" for t in task["tasks"])
    output_dir = task["output_dir"]
    
    return f"""你是一个专业的 AI 助手，负责执行以下高质量任务：

## 任务
{title}

## 描述
{description}

## 具体工作
{tasks_list}

## 输出要求
1. 所有输出保存到 `{output_dir}` 目录
2. 使用 Markdown 格式
3. 包含完整的元数据（标题、日期、作者等）
4. 内容要有深度和实用性
5. 代码要可运行，文档要完整

## 工作流程
1. 创建输出目录
2. 逐个完成上述任务
3. 每个任务完成后保存结果
4. 最后生成总结报告

## 质量标准
- 文章：至少 10000 字，结构完整，有数据支撑，深入分析每个方面
- 代码：可运行，有测试，有文档，包含详细注释
- 分析：有数据，有案例，有建议，全面覆盖各个维度
- 教程：有原理，有示例，有练习，循序渐进深入讲解

**重要：请尽可能详细地展开每个部分，目标是生成至少 10000 字的深度内容。不要省略任何细节，全面覆盖所有相关方面。**

请开始执行任务。"""

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
            {"role": "system", "content": "你是一个专业的 AI 助手，擅长执行复杂任务。请确保输出高质量、有深度、有实用价值的内容。**重要：请尽可能详细地展开每个部分，目标是生成至少 10000 字的深度内容。不要省略任何细节，全面覆盖所有相关方面。**"},
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
                timeout=aiohttp.ClientTimeout(total=600),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    usage = data.get("usage", {})
                    input_tokens = usage.get("prompt_tokens", 0)
                    output_tokens = usage.get("completion_tokens", 0)
                    total = input_tokens + output_tokens
                    
                    stats["total_tokens"] += total
                    stats["total_calls"] += 1
                    
                    return {
                        "success": True,
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": total,
                        "content": data["choices"][0]["message"]["content"],
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

async def execute_subtask(session: aiohttp.ClientSession, task: dict, subtask: str, stats: dict, output_dir: Path) -> dict:
    """执行单个子任务"""
    prompt = f"""请完成以下任务：

任务：{task['title']}
子任务：{subtask}

要求：
1. 详细完成任务
2. 输出高质量内容
3. 保存到指定目录

请开始执行："""
    
    result = await call_mimo(session, prompt, stats)
    
    if result["success"]:
        # 保存结果
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c for c in subtask[:30] if c.isalnum() or c in "._- ").strip()
        filename = f"{safe_name}.md"
        filepath = output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {subtask}\n\n")
            f.write(f"**任务**: {task['title']}\n")
            f.write(f"**时间**: {datetime.now().isoformat()}\n\n")
            f.write(result["content"])
        
        return {"success": True, "file": str(filepath), "tokens": result["total"]}
    
    return {"success": False, "error": result["error"]}

async def execute_task(agent_id: int, session: aiohttp.ClientSession, task: dict, stats: dict) -> dict:
    """执行完整任务（包含多个子任务）"""
    task_id = task["id"]
    title = task["title"]
    output_dir = PROJECTS_DIR / task["output_dir"].split("/")[-1]
    
    log(f"[Agent {agent_id:02d}] 开始执行: {title}")
    
    completed_subtasks = 0
    failed_subtasks = 0
    total_tokens = 0
    
    for subtask in task["tasks"]:
        result = await execute_subtask(session, task, subtask, stats, output_dir)
        
        if result["success"]:
            completed_subtasks += 1
            total_tokens += result["tokens"]
            log(f"[Agent {agent_id:02d}] ✓ 完成: {subtask[:50]}... | +{result['tokens']:,} tokens")
        else:
            failed_subtasks += 1
            log(f"[Agent {agent_id:02d}] ✗ 失败: {subtask[:50]}... | {result['error']}")
    
    # 生成任务总结
    summary = f"""# {title} - 执行总结

## 任务信息
- **ID**: {task_id}
- **类型**: {task['type']}
- **描述**: {task['description']}

## 执行结果
- **完成子任务**: {completed_subtasks}/{len(task['tasks'])}
- **失败子任务**: {failed_subtasks}
- **消耗 Tokens**: {total_tokens:,}

## 输出目录
{output_dir}

## 生成时间
{datetime.now().isoformat()}
"""
    
    summary_file = output_dir / "README.md"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary)
    
    return {
        "task_id": task_id,
        "title": title,
        "completed": completed_subtasks,
        "failed": failed_subtasks,
        "tokens": total_tokens,
        "output_dir": str(output_dir),
    }

async def agent_worker(agent_id: int, session: aiohttp.ClientSession, tasks: list, stats: dict, stop_event: asyncio.Event):
    """Agent Worker 协程"""
    while not stop_event.is_set():
        # 随机选择一个任务
        task = random.choice(tasks)
        
        try:
            result = await execute_task(agent_id, session, task, stats)
            
            if result["failed"] == 0:
                stats["completed_tasks"] += 1
                stats["task_history"].append({
                    "task_id": result["task_id"],
                    "status": "completed",
                    "tokens": result["tokens"],
                    "time": datetime.now().isoformat(),
                })
                log(f"[Agent {agent_id:02d}] ✅ 任务完成: {result['title']} | {result['tokens']:,} tokens")
            else:
                stats["failed_tasks"] += 1
                log(f"[Agent {agent_id:02d}] ⚠️ 任务部分完成: {result['title']} | {result['completed']}/{result['completed'] + result['failed']}")
        
        except Exception as e:
            log(f"[Agent {agent_id:02d}] ❌ 任务异常: {str(e)[:100]}")
            stats["errors"] += 1
        
        # 短暂休息，避免占用太多资源
        await asyncio.sleep(2)  # 恢复到2秒，确保不影响ClawX

async def stats_reporter(stats: dict, stop_event: asyncio.Event):
    """统计报告协程"""
    while not stop_event.is_set():
        await asyncio.sleep(600)  # 每10分钟报告
        
        elapsed = time.time() - stats.get("_start", time.time())
        hours = elapsed / 3600
        rate = stats["total_tokens"] / hours if hours > 0 else 0
        remaining = (TOTAL_TARGET - stats["total_tokens"]) / rate if rate > 0 else float('inf')
        
        log("=" * 70)
        log("📊 完美方案执行统计")
        log(f"  总 tokens: {stats['total_tokens']:,} / {TOTAL_TARGET:,} ({stats['total_tokens']/TOTAL_TARGET*100:.2f}%)")
        log(f"  完成任务: {stats['completed_tasks']}")
        log(f"  失败任务: {stats['failed_tasks']}")
        log(f"  API 调用: {stats['total_calls']:,}")
        log(f"  速率: {rate/1e6:.2f}M tokens/h")
        log(f"  运行时间: {hours:.2f} 小时")
        log(f"  预计剩余: {remaining:.2f} 小时 ({remaining/24:.1f} 天)")
        log(f"  错误: {stats['errors']}")
        log("=" * 70)
        
        save_stats(stats)

async def main():
    if not API_KEY:
        print("错误: 未设置 CUSTOM_API_KEY")
        return
    
    # 创建目录
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载任务
    tasks = load_tasks()
    
    log("=" * 70)
    log("🚀 MiMo 完美方案启动")
    log(f"目标: {TOTAL_TARGET/1e9:.0f}B tokens")
    log(f"任务数: {len(tasks)}")
    log(f"并发 Agent: {CONCURRENCY}")
    log("=" * 70)
    
    stats = load_stats()
    stats["_start"] = time.time()
    if not stats["start_time"]:
        stats["start_time"] = datetime.now().isoformat()
    
    stop_event = asyncio.Event()
    
    async with aiohttp.ClientSession() as session:
        agents = [
            asyncio.create_task(agent_worker(i, session, tasks, stats, stop_event))
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
            for a in agents:
                a.cancel()
            reporter.cancel()
            await asyncio.gather(*agents, reporter, return_exceptions=True)
            
            save_stats(stats)
            
            log("=" * 70)
            log("📋 最终统计")
            log(f"  总 tokens: {stats['total_tokens']:,}")
            log(f"  完成任务: {stats['completed_tasks']}")
            log(f"  失败任务: {stats['failed_tasks']}")
            log(f"  错误: {stats['errors']}")
            log("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
