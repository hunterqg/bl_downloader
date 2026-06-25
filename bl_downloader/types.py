from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class VideoQuality(IntEnum):
    _8K = 127
    HDR = 126
    _4K = 120
    _1080P_60 = 116
    _1080P_PLUS = 112
    _1080P = 80
    _720P_60 = 74
    _720P = 64
    _480P = 32
    _360P = 16


QUALITY_LABELS: dict[VideoQuality, str] = {
    VideoQuality._8K: '8K 超高清',
    VideoQuality.HDR: 'HDR 真彩',
    VideoQuality._4K: '4K 超高清',
    VideoQuality._1080P_60: '1080P 60帧',
    VideoQuality._1080P_PLUS: '1080P 高码率',
    VideoQuality._1080P: '1080P 高清',
    VideoQuality._720P_60: '720P 60帧',
    VideoQuality._720P: '720P 高清',
    VideoQuality._480P: '480P 清晰',
    VideoQuality._360P: '360P 流畅',
}


@dataclass
class VideoInfo:
    title: str
    duration: int
    uploader: str
    bvid: str
    cover_url: str
    description: str
    available_qualities: list[VideoQuality] = field(default_factory=list)


@dataclass
class DownloadProgress:
    percent: float
    speed: str
    stage: str


@dataclass
class DownloadResult:
    success: bool
    file_path: str = ''
    message: str = ''
