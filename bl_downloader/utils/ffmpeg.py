from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import sys
import threading
from collections.abc import Callable

from bl_downloader.errors import DownloadCancelled

logger = logging.getLogger(__name__)


class FFmpegError(Exception):
    ...


def _get_ffmpeg_path() -> str:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundled = os.path.join(sys._MEIPASS, 'ffmpeg.exe')
        if os.path.exists(bundled):
            return bundled

    exe_dir = os.path.dirname(sys.executable)
    local = os.path.join(exe_dir, 'ffmpeg.exe')
    if os.path.exists(local):
        return local

    which = shutil.which('ffmpeg')
    if which:
        return which

    raise FFmpegError('未找到 ffmpeg，请安装 ffmpeg 并确保其在 PATH 中')


def check_ffmpeg() -> str:
    ffmpeg_path = _get_ffmpeg_path()
    try:
        result = subprocess.run(
            [ffmpeg_path, '-version'],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode != 0:
            raise FFmpegError('ffmpeg 不可用')
        first_line = result.stdout.splitlines()[0]
        return first_line
    except FileNotFoundError as e:
        raise FFmpegError('未找到 ffmpeg，请安装 ffmpeg 并确保其在 PATH 中') from e


def merge_video_audio(
    video_path: str,
    audio_path: str,
    output_path: str,
    on_progress: Callable[[float], None] | None = None,
    stop_event: threading.Event | None = None,
) -> str:
    ffmpeg_path = _get_ffmpeg_path()
    logger.info('合并视频+音频: %s + %s -> %s', video_path, audio_path, output_path)
    cmd = [
        ffmpeg_path, '-y',
        '-i', video_path,
        '-i', audio_path,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-strict', 'experimental',
        '-movflags', '+faststart',
        output_path,
    ]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding='utf-8',
        errors='replace',
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    duration_pattern = re.compile(r'Duration: (\d+):(\d+):(\d+)\.(\d+)')
    time_pattern = re.compile(r'time=(\d+):(\d+):(\d+)\.(\d+)')
    total_ms: float | None = None

    if process.stderr:
        for line in iter(process.stderr.readline, ''):
            if stop_event is not None and stop_event.is_set():
                process.terminate()
                process.wait()
                raise DownloadCancelled('合并已取消')
            if total_ms is None:
                m = duration_pattern.search(line)
                if m:
                    total_ms = (
                        int(m.group(1)) * 3600000
                        + int(m.group(2)) * 60000
                        + int(m.group(3)) * 1000
                        + int(m.group(4)) * 10
                    )
            m = time_pattern.search(line)
            if m and total_ms and total_ms > 0:
                current_ms = (
                    int(m.group(1)) * 3600000
                    + int(m.group(2)) * 60000
                    + int(m.group(3)) * 1000
                    + int(m.group(4)) * 10
                )
                percent = min(current_ms / total_ms * 100, 100)
                if on_progress:
                    on_progress(percent)

    process.wait()
    if process.returncode != 0:
        error_output = process.stderr.read() if process.stderr else ''
        raise FFmpegError(f'FFmpeg 合并失败 (code {process.returncode}): {error_output[:200]}')

    return output_path
