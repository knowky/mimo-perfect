#!/usr/bin/env python3
"""
MiMo 完美方案 - 监控面板
"""

import json
import time
from datetime import datetime
from pathlib import Path

STATS_FILE = Path(__file__).parent / "perfect_stats.json"
PROJECTS_DIR = Path(__file__).parent / "projects"
TARGET = 38_000_000_000

def format_tokens(n: int) -> str:
    if n >= 1e9:
        return f"{n/1e9:.2f}B"
    elif n >= 1e6:
        return f"{n/1e6:.2f}M"
    elif n >= 1e3:
        return f"{n/1e3:.2f}K"
    return str(n)

def count_projects():
    if not PROJECTS_DIR.exists():
        return 0, 0
    
    total_files = 0
    total_dirs = 0
    
    for item in PROJECTS_DIR.iterdir():
        if item.is_dir():
            total_dirs += 1
            total_files += len(list(item.rglob("*.md")))
    
    return total_dirs, total_files

def main():
    print("MiMo 完美方案 - 监控面板")
    print("=" * 70)
    
    while True:
        try:
            if STATS_FILE.exists():
                with open(STATS_FILE, "r") as f:
                    stats = json.load(f)
                
                total = stats.get("total_tokens", 0)
                calls = stats.get("total_calls", 0)
                completed = stats.get("completed_tasks", 0)
                failed = stats.get("failed_tasks", 0)
                errors = stats.get("errors", 0)
                start = stats.get("start_time")
                last = stats.get("last_update")
                history = stats.get("task_history", [])
                
                if start:
                    start_dt = datetime.fromisoformat(start)
                    elapsed = (datetime.now() - start_dt).total_seconds()
                    hours = elapsed / 3600
                    rate = total / hours if hours > 0 else 0
                    remaining = (TARGET - total) / rate if rate > 0 else float('inf')
                else:
                    hours = 0
                    rate = 0
                    remaining = float('inf')
                
                project_dirs, project_files = count_projects()
                
                print("\033[2J\033[H", end="")
                print("MiMo 完美方案 - 监控面板")
                print("=" * 70)
                print()
                print("📊 执行进度")
                print(f"  目标:     {format_tokens(TARGET)} tokens")
                print(f"  当前:     {format_tokens(total)} tokens ({total/TARGET*100:.2f}%)")
                print(f"  剩余:     {format_tokens(TARGET - total)} tokens")
                print()
                print("📈 任务统计")
                print(f"  完成任务: {completed}")
                print(f"  失败任务: {failed}")
                print(f"  API 调用: {calls:,}")
                print(f"  错误:     {errors}")
                print()
                print("📁 项目统计")
                print(f"  项目目录: {project_dirs}")
                print(f"  生成文件: {project_files}")
                print()
                print("⏱️  性能指标")
                print(f"  速率:     {format_tokens(rate)} tokens/h")
                print(f"  运行时间: {hours:.2f} 小时")
                print(f"  预计完成: {remaining:.1f} 小时 ({remaining/24:.1f} 天)")
                print()
                
                if history:
                    print("📋 最近完成的任务")
                    for item in history[-5:]:
                        print(f"  {item['task_id']:20s} | {item['tokens']:>12,} tokens | {item['time'][:19]}")
                    print()
                
                print(f"  最后更新: {last}")
                print("=" * 70)
                print("按 Ctrl+C 退出监控")
            
            else:
                print("等待执行数据...")
            
            time.sleep(10)
        
        except KeyboardInterrupt:
            print("\n监控已退出")
            break
        except Exception as e:
            print(f"错误: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
