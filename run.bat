@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [*] 创建虚拟环境...
    python -m venv venv
)

echo [*] 安装依赖...
call venv\Scripts\activate.bat
python -m pip install -q --upgrade pip
pip install -q -e .

echo [*] 检查 ffmpeg...
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 未检测到 ffmpeg，音视频合并功能不可用
    echo     请从 https://ffmpeg.org/download.html 下载并添加到 PATH
    echo.
    pause
)

echo [*] 启动 bl_downloader...
python -m bl_downloader

pause
