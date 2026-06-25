#!/usr/bin/env bash
set -e

APP_NAME="bl_downloader"
VENV_DIR="venv"

cd "$(dirname "$0")"

if [ ! -d "$VENV_DIR" ]; then
    echo "[*] 创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
fi

echo "[*] 安装依赖..."
source "$VENV_DIR/bin/activate"
pip install -q --upgrade pip
pip install -q -e .

echo "[*] 检查系统依赖..."
if ! command -v ffmpeg &>/dev/null; then
    echo "[!] 未检测到 ffmpeg，音视频合并功能不可用"
    echo "    请安装: sudo apt install ffmpeg  (Ubuntu/Debian)"
    echo "          brew install ffmpeg       (macOS)"
    echo ""
    read -p "    按 Enter 继续启动，或 Ctrl+C 退出..."
fi

echo "[*] 启动 $APP_NAME..."
python -m "$APP_NAME"
