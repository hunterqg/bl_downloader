from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parent
    dist_dir = project_root / 'dist'
    app_dir = dist_dir / 'bl_downloader'

    print('[*] 安装/更新 PyInstaller...')
    subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '-q', 'pyinstaller'],
        check=True,
    )

    ffmpeg_path = shutil.which('ffmpeg')
    if not ffmpeg_path:
        print('[!] 错误: 未在系统 PATH 中找到 ffmpeg')
        print('   请先安装 ffmpeg 并确保其在 PATH 中')
        sys.exit(1)
    print(f'[*] 找到 ffmpeg: {ffmpeg_path}')

    if app_dir.exists():
        print('[*] 清理旧的打包目录...')
        shutil.rmtree(app_dir)

    print('[*] 使用 PyInstaller 打包...')
    pyinstaller = [sys.executable, '-m', 'PyInstaller']
    cmd = [
        *pyinstaller,
        '--name', 'bl_downloader',
        '--onedir',
        '--windowed',
        '--clean',
        '--noconfirm',
        '--add-data', f'{ffmpeg_path};.',
        '--hidden-import', 'bilibili_api',
        '--hidden-import', 'bilibili_api.video',
        '--hidden-import', 'bilibili_api.clients',
        '--hidden-import', 'bilibili_api.clients.HTTPXClient',
        '--hidden-import', 'bilibili_api.bangumi',
        '--hidden-import', 'httpx',
        str(project_root / 'bl_downloader' / '__main__.py'),
    ]
    subprocess.run(cmd, check=True, cwd=str(project_root))

    ffmpeg_dest = app_dir / 'ffmpeg.exe'
    shutil.copy2(ffmpeg_path, str(ffmpeg_dest))
    print(f'[*] ffmpeg 已复制到: {ffmpeg_dest}')

    print()
    print('=' * 50)
    print('打包完成!')
    print(f'输出目录: {app_dir}')
    print(f'可执行文件: {app_dir / "bl_downloader.exe"}')
    print(f'ffmpeg: {ffmpeg_dest}')
    print('=' * 50)


if __name__ == '__main__':
    main()
