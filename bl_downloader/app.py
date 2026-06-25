from __future__ import annotations

import asyncio
import logging
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from bl_downloader.services.downloader import (
    DownloadCancelled,
    DownloadError,
    download_video,
)
from bl_downloader.services.video_info import (
    VideoInfoError,
    format_duration,
    get_video_info,
    quality_display,
)
from bl_downloader.types import VideoQuality
from bl_downloader.utils.ffmpeg import FFmpegError, check_ffmpeg

logger = logging.getLogger(__name__)


class App:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title('B站视频下载器')
        self.root.geometry('680x620')
        self.root.minsize(580, 520)
        self.root.resizable(True, True)

        self.progress_queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._downloading = False

        self._build_ui()

        self.root.after(200, self._poll_progress)

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        # row 0: URL
        ttk.Label(frame, text='视频链接:').grid(row=0, column=0, sticky=tk.W, pady=(0, 4))
        url_row = ttk.Frame(frame)
        url_row.grid(row=0, column=1, columnspan=2, sticky=tk.EW, pady=(0, 8))
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_row, textvariable=self.url_var)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.parse_btn = ttk.Button(url_row, text='解析', command=self._on_parse)
        self.parse_btn.pack(side=tk.RIGHT, padx=(6, 0))
        self.url_entry.bind('<Return>', lambda e: self._on_parse())

        # row 1: video info
        self.info_frame = ttk.LabelFrame(frame, text='视频信息', padding=8)
        self.info_frame.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=(0, 8))
        self.info_frame.columnconfigure(1, weight=1)

        self.info_title_var = tk.StringVar(value='(等待解析...)')
        ttk.Label(self.info_frame, text='标题:').grid(row=0, column=0, sticky=tk.W)
        ttk.Label(self.info_frame, textvariable=self.info_title_var).grid(
            row=0, column=1, sticky=tk.W
        )

        self.info_uploader_var = tk.StringVar(value='')
        ttk.Label(self.info_frame, text='UP主:').grid(row=1, column=0, sticky=tk.W)
        ttk.Label(self.info_frame, textvariable=self.info_uploader_var).grid(
            row=1, column=1, sticky=tk.W
        )

        self.info_duration_var = tk.StringVar(value='')
        ttk.Label(self.info_frame, text='时长:').grid(row=2, column=0, sticky=tk.W)
        ttk.Label(self.info_frame, textvariable=self.info_duration_var).grid(
            row=2, column=1, sticky=tk.W
        )

        # row 2: quality
        ttk.Label(frame, text='清晰度:').grid(row=2, column=0, sticky=tk.W, pady=(0, 4))
        self.quality_var = tk.StringVar()
        self.quality_combo = ttk.Combobox(
            frame, textvariable=self.quality_var, state='readonly', width=30
        )
        self.quality_combo.grid(row=2, column=1, sticky=tk.W, pady=(0, 8))

        # row 3: save path
        ttk.Label(frame, text='保存到:').grid(row=3, column=0, sticky=tk.W, pady=(0, 4))
        path_row = ttk.Frame(frame)
        path_row.grid(row=3, column=1, columnspan=2, sticky=tk.EW, pady=(0, 8))
        self.path_var = tk.StringVar(value=os.path.expanduser('~/Downloads'))
        self.path_entry = ttk.Entry(path_row, textvariable=self.path_var)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.browse_btn = ttk.Button(path_row, text='浏览', command=self._on_browse)
        self.browse_btn.pack(side=tk.RIGHT, padx=(6, 0))

        # row 4: buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=(8, 4))
        self.download_btn = ttk.Button(
            btn_frame, text='开始下载', command=self._on_download, width=12
        )
        self.download_btn.pack(side=tk.LEFT, padx=4)
        self.cancel_btn = ttk.Button(
            btn_frame, text='停止下载', command=self._on_stop, width=12, state=tk.DISABLED
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=4)

        # row 5: progress bar
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(
            frame, variable=self.progress_var, maximum=100
        )
        self.progress_bar.grid(row=5, column=0, columnspan=3, sticky=tk.EW, pady=(4, 2))

        # row 6: status
        self.status_var = tk.StringVar(value='就绪')
        self.status_label = ttk.Label(frame, textvariable=self.status_var)
        self.status_label.grid(row=6, column=0, columnspan=3, sticky=tk.W, pady=(0, 4))

        # row 7: log
        log_frame = ttk.LabelFrame(frame, text='日志', padding=4)
        log_frame.grid(row=7, column=0, columnspan=3, sticky=tk.NSEW, pady=(4, 0))
        frame.rowconfigure(7, weight=1)
        frame.columnconfigure(1, weight=1)

        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def log(self, msg: str) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + '\n')
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _on_browse(self) -> None:
        path = filedialog.askdirectory(title='选择保存目录')
        if path:
            self.path_var.set(path)

    def _on_parse(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning('提示', '请输入视频链接')
            return
        self.parse_btn.configure(state=tk.DISABLED)
        self.info_title_var.set('正在解析...')
        self.status_var.set('解析中...')
        self.log(f'正在解析: {url}')

        def _fetch():
            async def _run():
                try:
                    info = await get_video_info(url)
                    self.root.after(0, self._on_parse_done, info)
                except VideoInfoError as e:
                    self.root.after(0, self._on_parse_error, str(e))
                except Exception as e:
                    self.root.after(0, self._on_parse_error, str(e))

            asyncio.run(_run())

        threading.Thread(target=_fetch, daemon=True).start()

    def _on_parse_done(self, info) -> None:
        self._current_video_info = info
        self.info_title_var.set(info.title)
        self.info_uploader_var.set(info.uploader)
        self.info_duration_var.set(format_duration(info.duration))
        self.log(f'解析成功: {info.title}')

        labels = [quality_display(q) for q in info.available_qualities]
        self.quality_combo['values'] = labels
        if labels:
            self.quality_var.set(labels[0])
        self.parse_btn.configure(state=tk.NORMAL)
        self.status_var.set('就绪，选择清晰度后开始下载')

    def _on_stop(self) -> None:
        self._stop_event.set()
        self.cancel_btn.configure(state=tk.DISABLED)
        self.status_var.set('正在停止...')
        self.log('用户请求停止下载')

    def _on_parse_error(self, msg: str) -> None:
        self.info_title_var.set('解析失败')
        self.status_var.set(f'错误: {msg}')
        self.log(f'解析失败: {msg}')
        self.parse_btn.configure(state=tk.NORMAL)

    def _on_download(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning('提示', '请输入视频链接')
            return
        save_dir = self.path_var.get().strip() or os.path.expanduser('~/Downloads')
        os.makedirs(save_dir, exist_ok=True)
        self.path_var.set(save_dir)
        quality_str = self.quality_var.get()
        if not quality_str:
            messagebox.showwarning('提示', '请先解析视频')
            return

        quality_code = int(quality_str.split('(')[-1].rstrip(')'))
        quality = VideoQuality(quality_code)

        self._downloading = True
        self._stop_event.clear()
        self.download_btn.configure(state=tk.DISABLED)
        self.cancel_btn.configure(state=tk.NORMAL)
        self.parse_btn.configure(state=tk.DISABLED)
        self.progress_var.set(0)
        self.status_var.set('准备下载...')
        self.log(f'开始下载: {quality_str}')

        def _run():
            async def _task():
                try:
                    final_path = await download_video(
                        url=url,
                        save_dir=save_dir,
                        quality=quality,
                        on_progress=lambda p, s: self.progress_queue.put(
                            {'type': 'progress', 'percent': p, 'speed': s}
                        ),
                        on_stage=lambda stage: self.progress_queue.put(
                            {'type': 'stage', 'stage': stage}
                        ),
                        stop_event=self._stop_event,
                    )
                    self.progress_queue.put({'type': 'complete', 'path': final_path})
                except DownloadCancelled:
                    self.progress_queue.put({'type': 'cancelled'})
                except (DownloadError, FFmpegError, VideoInfoError) as e:
                    self.progress_queue.put({'type': 'error', 'msg': str(e)})
                except Exception as e:
                    logger.exception('下载异常')
                    self.progress_queue.put({'type': 'error', 'msg': str(e)})

            asyncio.run(_task())

        threading.Thread(target=_run, daemon=True).start()

    def _poll_progress(self) -> None:
        try:
            while True:
                msg = self.progress_queue.get_nowait()
                t = msg.get('type', '')

                if t == 'progress':
                    percent = msg.get('percent', 0)
                    speed = msg.get('speed', '')
                    self.progress_var.set(percent)
                    if speed:
                        self.status_var.set(f'下载中... {percent:.1f}% ({speed})')
                    else:
                        self.status_var.set(f'处理中... {percent:.1f}%')
                elif t == 'stage':
                    self.status_var.set(msg.get('stage', ''))
                    self.log(msg.get('stage', ''))
                elif t == 'complete':
                    path = msg.get('path', '')
                    self.status_var.set('下载完成!')
                    self.progress_var.set(100)
                    self.log(f'下载完成: {path}')
                    self._downloading = False
                    self.download_btn.configure(state=tk.NORMAL)
                    self.cancel_btn.configure(state=tk.DISABLED)
                    self.parse_btn.configure(state=tk.NORMAL)
                    messagebox.showinfo('完成', f'视频已保存到:\n{path}')
                elif t == 'cancelled':
                    self.status_var.set('下载已取消')
                    self.log('下载已取消')
                    self._downloading = False
                    self.download_btn.configure(state=tk.NORMAL)
                    self.cancel_btn.configure(state=tk.DISABLED)
                    self.parse_btn.configure(state=tk.NORMAL)
                elif t == 'error':
                    err = msg.get('msg', '未知错误')
                    self.status_var.set('下载失败')
                    self.log(f'错误: {err}')
                    self._downloading = False
                    self.download_btn.configure(state=tk.NORMAL)
                    self.cancel_btn.configure(state=tk.DISABLED)
                    self.parse_btn.configure(state=tk.NORMAL)
                    messagebox.showerror('下载失败', err)
        except queue.Empty:
            pass

        self.root.after(200, self._poll_progress)

    def run(self) -> None:
        try:
            ffmpeg_ver = check_ffmpeg()
            self.log(f'FFmpeg: {ffmpeg_ver}')
        except FFmpegError as e:
            self.log(f'警告: {e}')
            messagebox.showwarning('FFmpeg 未安装', str(e))
        self.root.mainloop()
