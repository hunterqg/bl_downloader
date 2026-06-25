from __future__ import annotations

import logging
import sys


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S',
    )

    from bl_downloader.app import App

    app = App()
    app.run()


if __name__ == '__main__':
    sys.exit(main())
