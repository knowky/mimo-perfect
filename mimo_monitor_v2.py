#!/usr/bin/env python3
"""
MiMo Content Factory - 生产监控面板
"""

import json
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict

STATS_FILE = Path(__file__).parent / "factory_stats.json"
OUTPUT_DIR = Path(__file__).parent / "output"
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
    """统计已生成的内容"""
    if not OUTPUT_DIR.exists():
        return 0, {}
    
    total = 0
    by_category = defaultdict(int)
    
    for f in OUTPUT_DIR.rglob("*.md"):
        total += 1
        # 获取顶级分类
        parts = f.relative_to(OUTPUT_DIR).parts
        if len(parts) > 1:
            by_category[parts[0]] += 1
    
    return total, dict(by_category)

def main():
    print("MiMo Content Factory - 生产监控")
    print("=" * 70)
    
    while True:
        try:
            if STATS_FILE.exists():
                with open(STATS_FILE, "r") as f:
                    stats = json.load(f)
                
                total = stats.get("total_tokens", 0)
                calls = stats.get("total_calls", 0)
                content = stats.get("content_generated", 0)
                input_t = stats.get("total_input", 0)
                output_t = stats.get("total_output", 0)
                errors = stats.get("errors", 0)
                start = stats.get("start_time")
                last = stats.get("last_update")
                by_cat = stats.get("by_category", {})
                
                # 计算速率
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
                
                # 统计实际文件
                file_count, file_cats = count_content()
                
                # 清屏效果
                print("\033[2J\033[H", end="")
                print("MiMo Content Factory - 生产监控")
                print("=" * 70)
                print()
                print("📊 生产进度")
                print(f"  目标:     {format_tokens(TARGET)} tokens")
                print(f"  当前:     {format_tokens(total)} tokens ({total/TARGET*100:.2f}%)")
                print(f"  剩余:     {format_tokens(TARGET - total)} tokens")
                print()
                print("📈 生产统计")
                print(f"  API调用:  {calls:,} 次")
                print(f"  内容生成: {content} 篇")
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
                
                # 分类统计
                if by_cat:
                    print("📁 按类别统计 (API调用)")
                    for cat, data in sorted(by_cat.items(), key=lambda x: -x[1]["tokens"]):
                        print(f"  {cat:30s} | {data['calls']:>6} 次 | {format_tokens(data['tokens']):>10}")
                    print()
                
                if file_cats:
                    print("📂 按类别统计 (文件)")
                    for cat, count in sorted(file_cats.items(), key=lambda x: -x[1]):
                        print(f"  {cat:30s} | {count:>6} 个")
                
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
