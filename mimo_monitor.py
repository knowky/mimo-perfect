#!/usr/bin/env python3
"""
MiMo Token Burner - 监控面板
实时显示消耗进度和统计
"""

import json
import time
from datetime import datetime
from pathlib import Path

STATS_FILE = Path(__file__).parent / "burn_stats.json"
TARGET = 38_000_000_000

def format_tokens(n: int) -> str:
    if n >= 1e9:
        return f"{n/1e9:.2f}B"
    elif n >= 1e6:
        return f"{n/1e6:.2f}M"
    elif n >= 1e3:
        return f"{n/1e3:.2f}K"
    return str(n)

def main():
    print("MiMo Token Burner - 监控面板")
    print("=" * 60)
    
    while True:
        try:
            if STATS_FILE.exists():
                with open(STATS_FILE, "r") as f:
                    stats = json.load(f)
                
                total = stats.get("total_tokens", 0)
                calls = stats.get("total_calls", 0)
                input_t = stats.get("total_input", 0)
                output_t = stats.get("total_output", 0)
                errors = stats.get("errors", 0)
                start = stats.get("start_time")
                last = stats.get("last_update")
                
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
                
                # 清屏效果
                print("\033[2J\033[H", end="")
                print("MiMo Token Burner - 监控面板")
                print("=" * 60)
                print(f"  目标:     {format_tokens(TARGET)} tokens")
                print(f"  当前:     {format_tokens(total)} tokens ({total/TARGET*100:.2f}%)")
                print(f"  剩余:     {format_tokens(TARGET - total)} tokens")
                print()
                print(f"  调用次数: {calls:,}")
                print(f"  输入:     {format_tokens(input_t)} tokens")
                print(f"  输出:     {format_tokens(output_t)} tokens")
                print(f"  错误:     {errors:,}")
                print()
                print(f"  速率:     {format_tokens(rate)} tokens/h")
                print(f"  运行时间: {hours:.2f} 小时")
                print(f"  预计完成: {remaining:.1f} 小时 ({remaining/24:.1f} 天)")
                print()
                print(f"  最后更新: {last}")
                print("=" * 60)
                print("按 Ctrl+C 退出监控")
            
            else:
                print("等待统计数据...")
            
            time.sleep(5)
        
        except KeyboardInterrupt:
            print("\n监控已退出")
            break
        except Exception as e:
            print(f"错误: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
