# Bilibili Downloader | B站视频下载器

一个带桌面图形界面的 B站视频下载工具。

## 功能

- **图形界面** — 输入链接、选择清晰度、一键下载
- **清晰度选择** — 支持 360P 到 8K（取决于视频源）
- **进度跟踪** — 实时显示下载速度和百分比
- **停止下载** — 随时取消正在进行的下载任务
- **自动合并** — DASH 音视频流自动通过 FFmpeg 合并
- **跨平台** — 支持 Windows、macOS、Linux

## 快速启动

```bash
# Linux / macOS
./run.sh

# Windows
双击运行 run.bat
```

## 手动安装

```bash
python3 -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate    # Windows
pip install -e .
python -m bl_downloader
```

## 系统要求

- Python >= 3.10
- FFmpeg（用于音视频合并）
  - Linux: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: 从 https://ffmpeg.org/download.html 下载并配置 PATH

## 依赖

- `bilibili-api-python` — B站 API 客户端
- `httpx` — 异步 HTTP 下载

## 许可证

MIT
