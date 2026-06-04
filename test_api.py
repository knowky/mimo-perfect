#!/usr/bin/env python3
"""测试 MiMo API 连接"""

import asyncio
import aiohttp
import os
import json

API_BASE = "https://token-plan-cn.xiaomimimo.com/v1"
API_KEY = os.environ.get("CUSTOM_API_KEY", "")
MODEL = "mimo-v2.5-pro"

async def test():
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一个专业的AI助手。"},
            {"role": "user", "content": "请用100字介绍量子计算。"},
        ],
        "max_tokens": 200,
        "temperature": 0.7,
        "stream": False,
    }
    
    print(f"API: {API_BASE}")
    print(f"Model: {MODEL}")
    print(f"Key: {API_KEY[:10]}...")
    print()
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_BASE}/chat/completions",
            headers=headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            print(f"Status: {resp.status}")
            data = await resp.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if "usage" in data:
                usage = data["usage"]
                print(f"\nTokens used:")
                print(f"  Input: {usage.get('prompt_tokens', 0)}")
                print(f"  Output: {usage.get('completion_tokens', 0)}")
                print(f"  Total: {usage.get('total_tokens', 0)}")

if __name__ == "__main__":
    asyncio.run(test())
