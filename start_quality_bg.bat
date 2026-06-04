@echo off
REM MiMo 高质量内容生产 - 后台启动

cd /d "%~dp0"

echo 启动 MiMo 高质量内容生产系统...
echo 日志: quality_output.txt
echo 统计: quality_stats.json
echo.

start "MiMo Quality" /b python mimo_quality.py > quality_output.txt 2>&1

echo 后台进程已启动
echo.
echo 查看日志: type quality_output.txt
echo 查看统计: python mimo_quality_monitor.py
echo 停止进程: taskkill /f /im python.exe /fi "WINDOWTITLE eq MiMo Quality*"
echo.

pause
