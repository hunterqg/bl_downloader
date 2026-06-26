from __future__ import annotations

import logging
import sys


def main() -> None:
    """应用程序入口：初始化日志配置并启动主窗口"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    from bl_downloader.app import App

    app = App()
    app.run()


if __name__ == "__main__":
    main()
    sys.exit(0)
