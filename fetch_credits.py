#!/usr/bin/env python3
"""抓取小米开放平台 credits 数据"""

import requests
import json
from pathlib import Path

# 小米开放平台 API
API_URL = "https://platform.xiaomimimo.com/api/user/plan-info"
USER_ID = "3215035002"

def get_credits():
    """获取 credits 使用情况"""
    try:
        # 尝试直接访问 API
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        
        # 尝试不同的 API 端点
        endpoints = [
            f"https://platform.xiaomimimo.com/api/user/plan?userId={USER_ID}",
            f"https://platform.xiaomimimo.com/api/console/plan-manage?userId={USER_ID}",
            f"https://platform.xiaomimimo.com/api/user/info?userId={USER_ID}",
        ]
        
        for url in endpoints:
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    print(f"成功: {url}")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    return data
            except Exception as e:
                print(f"失败 {url}: {e}")
        
        print("所有 API 端点都失败了")
        return None
        
    except Exception as e:
        print(f"错误: {e}")
        return None

if __name__ == "__main__":
    print("正在抓取小米开放平台数据...")
    data = get_credits()
    
    if data:
        # 保存数据
        with open("xiaomi_credits.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("\n数据已保存到 xiaomi_credits.json")
    else:
        print("\n无法获取数据，需要登录或提供 cookies")
