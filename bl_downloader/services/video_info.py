from __future__ import annotations

import re

from bilibili_api import video as bili_video
from bilibili_api.video import (
    AudioStreamDownloadURL,
    VideoStreamDownloadURL,
)

from bl_downloader.types import QUALITY_LABELS, VideoInfo, VideoQuality


class VideoInfoError(Exception):
    ...


_BVID_PATTERN = re.compile(r'BV[a-zA-Z0-9]{10,}')
_AID_PATTERN = re.compile(r'av(\d+)', re.IGNORECASE)
_EP_PATTERN = re.compile(r'ep(\d+)', re.IGNORECASE)
_SS_PATTERN = re.compile(r'ss(\d+)', re.IGNORECASE)


def parse_url(url: str) -> tuple[str, str | int]:
    m = _BVID_PATTERN.search(url)
    if m:
        return 'bvid', m.group(0)
    m = _AID_PATTERN.search(url)
    if m:
        return 'aid', int(m.group(1))
    m = _EP_PATTERN.search(url)
    if m:
        return 'ep_id', int(m.group(1))
    m = _SS_PATTERN.search(url)
    if m:
        return 'ss_id', int(m.group(1))
    raise VideoInfoError(f'无法解析 URL: {url}')


def _create_video(key: str, value: str | int):
    kwargs = {key: value}
    return bili_video.Video(**kwargs)


async def get_video_info(url: str) -> VideoInfo:
    key, value = parse_url(url)
    v = _create_video(key, value)
    info = await v.get_info()

    download_data = await v.get_download_url(page_index=0)
    detector = bili_video.VideoDownloadURLDataDetecter(data=download_data)
    raw_qualities: set[int] = set()

    if detector.check_flv_mp4_stream():
        raw_qs: list[int] = download_data.get('accept_quality', [])
        raw_qualities.update(raw_qs)
    else:
        all_streams = detector.detect_all()
        for stream in all_streams:
            if isinstance(stream, VideoStreamDownloadURL):
                raw_qualities.add(stream.video_quality.value)
            elif isinstance(stream, AudioStreamDownloadURL):
                raw_qualities.add(stream.audio_quality.value)

    available = [q for q in VideoQuality if q.value in raw_qualities]
    available.sort(key=lambda q: q.value, reverse=True)

    title: str = info['title']
    duration: int = info.get('duration', 0)
    uploader: str = info.get('owner', {}).get('name', '')
    bvid: str = info.get('bvid', '')
    cover_url: str = info.get('pic', '')
    description: str = info.get('desc', '')

    return VideoInfo(
        title=title,
        duration=duration,
        uploader=uploader,
        bvid=bvid,
        cover_url=cover_url,
        description=description,
        available_qualities=available,
    )


def format_duration(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f'{h}:{m:02d}:{s:02d}'
    return f'{m}:{s:02d}'


def quality_display(q: VideoQuality) -> str:
    label = QUALITY_LABELS.get(q, f'未知 ({q.value})')
    return f'{label} ({q.value})'
