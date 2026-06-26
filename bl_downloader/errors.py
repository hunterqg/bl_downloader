from __future__ import annotations


class DownloadError(Exception):
    """下载过程中的通用异常"""


class DownloadCancelled(Exception):
    """用户取消下载时抛出的异常"""
