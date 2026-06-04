@echo off
REM MiMo 完美方案 - 后台启动

cd /d "%~dp0"

echo 启动 MiMo 完美方案...
echo 日志: perfect_output.txt
echo 统计: perfect_stats.json
echo 项目: projects/
echo.

start "MiMo Perfect" /b python mimo_perfect.py > perfect_output.txt 2>&1

echo 后台进程已启动
echo.
echo 查看日志: type perfect_output.txt
echo 查看统计: python mimo_perfect_monitor.py
echo 查看项目: dir projects
echo 停止进程: taskkill /f /im python.exe /fi "WINDOWTITLE eq MiMo Perfect*"
echo.

pause
