@echo off
REM MiMo Token Burner - Windows 启动脚本
REM 后台运行 burner，日志输出到文件

cd /d "%~dp0"

echo ============================================
echo MiMo Token Burner
echo ============================================
echo 目标: 38B tokens, 6天
echo 并发: 50
echo.
echo 按 Ctrl+C 停止
echo ============================================

python mimo_burner.py

pause
