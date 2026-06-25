# Bilibili Downloader

A desktop GUI tool for downloading Bilibili videos.

## Features

- **Graphical interface** — enter URL, select quality, start download
- **Quality selection** — supports 360P up to 8K (depending on video source)
- **Progress tracking** — real-time download speed and percentage display
- **Stop download** — cancel an ongoing download at any time
- **Auto merge** — automatically merges DASH video + audio streams via FFmpeg
- **Cross-platform** — runs on Windows, macOS, and Linux

## Quick Start

```bash
# Linux / macOS
./run.sh

# Windows
double-click run.bat
```

## Manual Setup

```bash
python3 -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate    # Windows
pip install -e .
python -m bl_downloader
```

## Requirements

- Python >= 3.10
- FFmpeg (for video/audio merging)

## Dependencies

- `bilibili-api-python` — Bilibili API client
- `httpx` — async HTTP downloads

## License

MIT
