from __future__ import annotations

import asyncio
import io
import logging
import queue
import threading
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from bilibili_api import Credential
from bilibili_api.login_v2 import QrCodeLogin, QrCodeLoginEvents

logger = logging.getLogger(__name__)


class LoginWindow(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Tk,
        on_done: Callable[[Credential], None],
    ) -> None:
        super().__init__(parent)
        self.title("B站扫码登录")
        self.geometry("320x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._on_done = on_done
        self._queue: queue.Queue = queue.Queue()
        self._qr_login = QrCodeLogin()
        self._running = True

        self._build_ui()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.after(200, self._poll)
        self._start_login()

    def _build_ui(self) -> None:
        self.qr_label = ttk.Label(self)
        self.qr_label.pack(pady=(24, 8))

        self.status_var = tk.StringVar(value="正在获取二维码...")
        ttk.Label(self, textvariable=self.status_var, wraplength=280).pack(pady=(4, 4))

        self.retry_btn = ttk.Button(
            self, text="重新获取", command=self._on_retry, state=tk.DISABLED
        )
        self.retry_btn.pack(pady=(4, 16))

    def _start_login(self) -> None:
        self.status_var.set("正在获取二维码...")
        self.retry_btn.configure(state=tk.DISABLED)

        def run():
            async def go():
                try:
                    await self._qr_login.generate_qrcode()
                except Exception as e:
                    self._queue.put(("error", str(e)))
                    return

                pic = self._qr_login.get_qrcode_picture()
                self._queue.put(("qr", pic.content))

                while self._running:
                    try:
                        status = await self._qr_login.check_state()
                    except Exception as e:
                        self._queue.put(("error", str(e)))
                        break

                    self._queue.put(("status", status))

                    if status == QrCodeLoginEvents.DONE:
                        cred = self._qr_login.get_credential()
                        self._queue.put(("cred", cred))
                        break
                    if status == QrCodeLoginEvents.TIMEOUT:
                        self._queue.put(("timeout", None))
                        break

                    await asyncio.sleep(1)

            asyncio.run(go())

        threading.Thread(target=run, daemon=True).start()

    def _poll(self) -> None:
        try:
            while True:
                msg, data = self._queue.get_nowait()

                if msg == "qr":
                    self._show_qr(data)
                    self.status_var.set("请使用 Bilibili App 扫码登录")
                elif msg == "status":
                    self._on_status(data)
                elif msg == "cred":
                    self.status_var.set("登录成功！")
                    self.after(500, self._on_success, data)
                elif msg == "timeout":
                    self.status_var.set("二维码已过期")
                    self.retry_btn.configure(state=tk.NORMAL)
                elif msg == "error":
                    self.status_var.set(f"错误: {data}")
                    self.retry_btn.configure(state=tk.NORMAL)
        except queue.Empty:
            pass

        if self._running:
            self.after(200, self._poll)

    def _show_qr(self, png_bytes: bytes) -> None:
        try:
            from PIL import Image, ImageTk

            pil_img = Image.open(io.BytesIO(png_bytes))
            pil_img = pil_img.resize((240, 240), Image.Resampling.NEAREST)  # type: ignore[arg-type,assignment]
            tk_img = ImageTk.PhotoImage(pil_img)
            self.qr_label.config(image=tk_img)
            self.qr_label.image = tk_img  # type: ignore[attr-defined]
        except Exception:
            self.status_var.set("显示二维码失败，请检查网络连接")

    def _on_status(self, status: QrCodeLoginEvents) -> None:
        labels = {
            QrCodeLoginEvents.SCAN: "等待扫码...",
            QrCodeLoginEvents.CONF: "已扫码，请在手机上确认",
        }
        if status in labels:
            self.status_var.set(labels[status])

    def _on_success(self, cred: Credential) -> None:
        self._running = False
        self._on_done(cred)
        self.destroy()

    def _on_retry(self) -> None:
        self._qr_login = QrCodeLogin()
        self._start_login()

    def _on_close(self) -> None:
        self._running = False
        self.destroy()
