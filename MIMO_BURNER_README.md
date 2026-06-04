# MiMo Token Burner

## 🎯 目标
6天内用完 38,000,000,000 (38B) tokens

## 📊 方案分析

| 方案 | 并发 | 吞吐量 | 完成时间 |
|------|------|--------|----------|
| 直接API (5k+8k) | 50 | 234M/h | 6.8天 ❌ |
| 直接API (5k+8k) | 100 | 468M/h | 3.4天 ✅ |
| 超大上下文 (150k+8k) | 50 | 632M/h | 2.5天 ✅ |

**推荐方案: 50-100并发直接调用 MiMo API**

## 🚀 使用方法

### 1. 启动 burner
```bash
cd scripts
python mimo_burner.py
```

### 2. 监控进度
```bash
python mimo_monitor.py
```

### 3. 调整并发数
编辑 `mimo_burner.py`，修改 `CONCURRENCY` 变量：
- 保守: 20-30
- 标准: 50
- 激进: 100-200

## 📁 文件说明

- `mimo_burner.py` - 主程序，执行 token 消耗
- `mimo_monitor.py` - 监控面板，实时显示进度
- `burn_stats.json` - 统计数据（自动生成）
- `burn_log.txt` - 运行日志（自动生成）

## ⚙️ 配置参数

在 `mimo_burner.py` 中：

```python
CONCURRENCY = 50          # 并发数
MAX_OUTPUT_TOKENS = 8000  # 每次输出 tokens
MAX_INPUT_TOKENS = 5000   # 每次输入 tokens
```

## 📈 性能估算

默认配置 (50并发):
- 每次调用: 13k tokens (5k in + 8k out)
- 每小时调用: 22,500 次
- 每小时消耗: 292.5M tokens
- 完成时间: 5.4 天

100并发:
- 每小时消耗: 585M tokens
- 完成时间: 2.7 天

## 🔧 API 参数

- API: https://token-plan-cn.xiaomimimo.com/v1
- Model: mimo-v2.5-pro
- Context Window: 200,000 tokens
- Max Output: 8,192 tokens
- 费用: 免费

## ⚠️ 注意事项

1. **网络稳定性**: 确保网络连接稳定
2. **API 限制**: 如遇 rate limit，降低并发数
3. **中断恢复**: 统计数据自动保存，可随时中断和恢复
4. **资源消耗**: 高并发会消耗较多 CPU 和内存

## 🎉 目标达成

当消耗达到 38B tokens 时，程序会自动停止并显示最终统计。

## 📞 问题排查

1. **API Key 错误**: 确保环境变量 `CUSTOM_API_KEY` 已设置
2. **连接超时**: 检查网络，或降低并发数
3. **Rate Limit**: 降低并发数或添加延迟

## 🔄 后台运行

### Windows
```bash
start /b python mimo_burner.py > burner_output.txt 2>&1
```

### Linux/Mac
```bash
nohup python mimo_burner.py > burner_output.txt 2>&1 &
```

或使用 tmux/screen
```bash
tmux new -s burner
python mimo_burner.py
# Ctrl+B, D 断开
# tmux attach -t burner 重新连接
```
