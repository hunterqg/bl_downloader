from __future__ import annotations

import logging
import os
import threading
import time
from collections.abc import Callable
from pathlib import Path

from bilibili_api import HEADERS
from bilibili_api import video as bili_video
from bilibili_api.video import AudioQuality
from httpx import AsyncClient

from bl_downloader.errors import DownloadCancelled, DownloadError
from bl_downloader.services.video_info import _create_video, parse_url
from bl_downloader.types import VideoQuality
from bl_downloader.utils.ffmpeg import check_ffmpeg, merge_video_audio

logger = logging.getLogger(__name__)


ProgressCallback = Callable[[float, str], None]
StageCallback = Callable[[str], None]


def _sanitize_filename(name: str) -> str:
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, '_')
    name = name.strip() or 'video'
    return name[:10]


async def _download_stream(
    client: AsyncClient,
    url: str,
    save_path: str,
    label: str,
    on_progress: ProgressCallback,
    stop_event: threading.Event,
) -> str:
    logger.info('开始下载 %s -> %s', label, save_path)
    async with client.stream('GET', url) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get('content-length', 0))
        downloaded = 0
        start_time = time.monotonic()
        last_report = start_time

        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, 'wb') as f:
            async for chunk in resp.aiter_bytes():
                if stop_event.is_set():
                    raise DownloadCancelled('下载已取消')
                f.write(chunk)
                downloaded += len(chunk)
                now = time.monotonic()
                if now - last_report >= 0.15 or downloaded >= total:
                    last_report = now
                    if total:
                        percent = downloaded / total * 100
                    else:
                        percent = 0.0
                    elapsed = now - start_time
                    speed = downloaded / elapsed / 1024 / 1024 if elapsed else 0
                    on_progress(percent, f'{speed:.1f} MB/s')

    return save_path


async def download_video(
    url: str,
    save_dir: str,
    quality: VideoQuality,
    on_progress: ProgressCallback,
    on_stage: StageCallback,
    stop_event: threading.Event,
    sessdata: str = '',
) -> str:
    check_ffmpeg()

    key, value = parse_url(url)
    credential = None
    if sessdata:
        from bilibili_api import Credential
        credential = Credential(sessdata=sessdata)

    v = _create_video(key, value)
    if credential:
        v.credential = credential

    if stop_event.is_set():
        raise DownloadCancelled()

    on_stage('获取视频信息...')
    info = await v.get_info()
    title = _sanitize_filename(info['title'])
    bvid: str = info.get('bvid', str(value))
    logger.info('视频: %s (%s)', title, bvid)

    if stop_event.is_set():
        raise DownloadCancelled()

    on_stage('获取下载地址...')
    download_data = await v.get_download_url(page_index=0)
    detector = bili_video.VideoDownloadURLDataDetecter(data=download_data)

    combined = detector.check_flv_mp4_stream()

    streams = detector.detect_best_streams(
        video_max_quality=quality,
        audio_max_quality=AudioQuality._192K,
        no_dolby_audio=True,
        no_hires=True,
    )
    if not streams:
        raise DownloadError('未找到可用的视频流')

    if stop_event.is_set():
        raise DownloadCancelled()

    os.makedirs(save_dir, exist_ok=True)

    async with AsyncClient(headers=HEADERS, timeout=30) as client:
        if combined:
            stream_url: str = streams[0].url
            video_path = os.path.join(save_dir, f'{title}.mp4')
            on_stage('下载视频...')
            await _download_stream(client, stream_url, video_path, '视频', on_progress, stop_event)
            final_path = video_path
        else:
            video_stream = streams[0]
            audio_stream = streams[1] if len(streams) > 1 else None

            temp_dir = os.path.join(save_dir, '_temp')
            os.makedirs(temp_dir, exist_ok=True)
            video_path = os.path.join(temp_dir, 'video.m4s')
            audio_path = os.path.join(temp_dir, 'audio.m4s') if audio_stream else ''

            if video_stream:
                on_stage('下载视频流...')
                await _download_stream(
                    client, video_stream.url, video_path, '视频流', on_progress, stop_event,
                )

            if audio_stream:
                on_stage('下载音频流...')
                await _download_stream(
                    client, audio_stream.url, audio_path, '音频流', on_progress, stop_event,
                )

            final_path = os.path.join(save_dir, f'{title}.mp4')
            on_stage('正在合并音视频...')
            merge_video_audio(
                video_path,
                audio_path,
                final_path,
                on_progress=lambda p: on_progress(p, ''),
                stop_event=stop_event,
            )

            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    return final_path
