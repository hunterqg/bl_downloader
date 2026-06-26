from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class VideoQuality(IntEnum):
    """B站视频清晰度枚举，值对应 Bilibili API 中的 quality 参数"""

    # 注意：Python 不允许以数字开头的枚举成员名，故加下划线前缀
    _8K = 127
    DOLBY = 126
    HDR = 125
    _4K = 120
    _1080P_60 = 116
    _1080P_PLUS = 112
    AI_REPAIR = 100
    _1080P = 80
    _720P_60 = 74
    _720P = 64
    _480P = 32
    _360P = 16


QUALITY_LABELS: dict[VideoQuality, str] = {
    # 清晰度枚举 -> 中文显示标签的映射
    VideoQuality._8K: "8K 超高清",
    VideoQuality.DOLBY: "杜比视界",
    VideoQuality.HDR: "HDR 真彩",
    VideoQuality._4K: "4K 超高清",
    VideoQuality._1080P_60: "1080P 60帧",
    VideoQuality._1080P_PLUS: "1080P 高码率",
    VideoQuality.AI_REPAIR: "AI 修复",
    VideoQuality._1080P: "1080P 高清",
    VideoQuality._720P_60: "720P 60帧",
    VideoQuality._720P: "720P 高清",
    VideoQuality._480P: "480P 清晰",
    VideoQuality._360P: "360P 流畅",
}


@dataclass
class VideoInfo:
    """解析后得到的视频元数据"""

    title: str
    duration: int
    uploader: str
    bvid: str
    cover_url: str
    description: str
    available_qualities: list[VideoQuality] = field(default_factory=list)


@dataclass
class DownloadProgress:
    """下载进度数据，用于在后台线程和 GUI 之间传递"""

    percent: float
    speed: str
    stage: str


@dataclass
class DownloadResult:
    """下载操作的最终结果"""

    success: bool
    file_path: str = ""
    message: str = ""
