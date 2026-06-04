#!/usr/bin/env python3
"""
MiMo 高质量内容生产 - 监控面板
"""

import json
import time
from datetime import datetime
from pathlib import Path

STATS_FILE = Path(__file__).parent / "quality_stats.json"
OUTPUT_DIR = Path(__file__).parent / "quality_output"
TARGET = 38_000_000_000

def format_tokens(n: int) -> str:
    if n >= 1e9:
        return f"{n/1e9:.2f}B"
    elif n >= 1e6:
        return f"{n/1e6:.2f}M"
    elif n >= 1e3:
        return f"{n/1e3:.2f}K"
    return str(n)

def count_content():
    if not OUTPUT_DIR.exists():
        return 0, {}
    
    total = 0
    by_type = {}
    
    for f in OUTPUT_DIR.rglob("*_v3.md"):  # 只统计终稿
        total += 1
        parts = f.relative_to(OUTPUT_DIR).parts
        if len(parts) > 1:
            by_type[parts[0]] = by_type.get(parts[0], 0) + 1
    
    return total, by_type

def main():
    print("MiMo 高质量内容生产 - 监控面板")
    print("=" * 70)
    
    while True:
        try:
            if STATS_FILE.exists():
                with open(STATS_FILE, "r") as f:
                    stats = json.load(f)
                
                total = stats.get("total_tokens", 0)
                calls = stats.get("total_calls", 0)
                content = stats.get("content_generated", 0)
                iterations = stats.get("quality_iterations", 0)
                input_t = stats.get("total_input", 0)
                output_t = stats.get("total_output", 0)
                errors = stats.get("errors", 0)
                start = stats.get("start_time")
                last = stats.get("last_update")
                by_type = stats.get("by_type", {})
                
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
                
                file_count, file_types = count_content()
                
                print("\033[2J\033[H", end="")
                print("MiMo 高质量内容生产 - 监控面板")
                print("=" * 70)
                print()
                print("📊 生产进度")
                print(f"  目标:     {format_tokens(TARGET)} tokens")
                print(f"  当前:     {format_tokens(total)} tokens ({total/TARGET*100:.2f}%)")
                print(f"  剩余:     {format_tokens(TARGET - total)} tokens")
                print()
                print("📈 生产统计")
                print(f"  API调用:  {calls:,} 次")
                print(f"  内容生成: {content} 篇 (终稿)")
                print(f"  质量迭代: {iterations} 次")
                print(f"  文件保存: {file_count} 个")
                print(f"  输入:     {format_tokens(input_t)} tokens")
                print(f"  输出:     {format_tokens(output_t)} tokens")
                print(f"  错误:     {errors:,} 次")
                print()
                print("⏱️  性能指标")
                print(f"  速率:     {format_tokens(rate)} tokens/h")
                print(f"  运行时间: {hours:.2f} 小时")
                print(f"  预计完成: {remaining:.1f} 小时 ({remaining/24:.1f} 天)")
                print()
                
                if by_type:
                    print("📁 按类型统计")
                    for t, data in sorted(by_type.items(), key=lambda x: -x[1]["tokens"]):
                        print(f"  {t:30s} | {data['count']:>5} 篇 | {format_tokens(data['tokens']):>10}")
                    print()
                
                if file_types:
                    print("📂 终稿文件")
                    for t, count in sorted(file_types.items(), key=lambda x: -x[1]):
                        print(f"  {t:30s} | {count:>5} 个")
                
                print()
                print(f"  最后更新: {last}")
                print("=" * 70)
                print("按 Ctrl+C 退出监控")
            
            else:
                print("等待生产数据...")
            
            time.sleep(10)
        
        except KeyboardInterrupt:
            print("\n监控已退出")
            break
        except Exception as e:
            print(f"错误: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
