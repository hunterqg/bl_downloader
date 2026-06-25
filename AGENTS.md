# AGENTS.md

## Build / Lint / Test Commands

### Prerequisites
- Python >= 3.10, pip, ffmpeg (system PATH)

### One-click run
./run.sh

### Manual run (after activating venv)
source venv/bin/activate
python -m bl_downloader

### Install dependencies
pip install -e .

### Install dev dependencies
pip install -e ".[dev]"

### Lint all files
ruff check .

### Format all files
ruff format .

### Type-check
mypy bl_downloader

### Run all tests
pytest

### Run a single test file
pytest tests/test_file.py

### Run a single test (by name pattern)
pytest -k "test_download_video"

### Run tests with coverage
pytest --cov=bl_downloader

---

## Code Style Guidelines

### Imports / Modules
- Use `from __future__ import annotations` at the top of every file.
- Order imports in groups, separated by a blank line:
  1. Python standard library (`os`, `pathlib`, `re`, `queue`)
  2. Third-party packages (`httpx`, `bilibili_api`)
  3. Internal imports (`bl_downloader.types`, `.services.downloader`)
- Use absolute imports for internal references (`bl_downloader.types`).
- Avoid `from module import *`.
- Prefer `from collections.abc import Callable, Iterator` over `typing.Callable`.

### Formatting
- Line length: 100. Use `ruff format` for auto-formatting.
- Use 4 spaces for indentation (never tabs).
- Use double quotes for strings that contain single quotes, single quotes otherwise.

### Types
- Use type hints for all function signatures and public class attributes.
- Prefer `|` union syntax (`str | None`) over `Optional[str]`.
- Prefer `list[X]` over `List[X]`, `dict[K, V]` over `Dict[K, V]` (Python 3.10+).
- Use `@dataclass` for data containers, `Enum` / `IntEnum` for constants.
- Avoid `Any`; use `object` or proper union types instead.

### Naming Conventions
- **Files/Directories**: `snake_case` (`video_info.py`, `downloader.py`).
- **Classes**: `PascalCase` (`VideoInfoFetcher`, `DownloadManager`).
- **Functions/Methods**: `snake_case` (`get_video_info`, `start_download`).
- **Variables**: `snake_case` (`save_path`, `max_retries`).
- **Constants (module-level)**: `UPPER_SNAKE_CASE` (`QUALITY_LABELS`, `DEFAULT_TIMEOUT`).
- **Private methods/attributes**: Prefix with `_` (`_parse_url`, `_video_path`).

### Error Handling
- Define custom exception classes in `bl_downloader/errors.py` when needed.
- Catch specific exceptions, never bare `except:`.
- For expected failures (network error, invalid URL), raise typed exceptions.
- For unexpected errors, log and re-raise to let the GUI surface the message.
- Validate inputs at the boundary (URL format, file path writability, ffmpeg availability).

### Logging
- Use `logging.getLogger(__name__)` in each module.
- Configure logging at the application entry point (`__main__.py`).
- Log levels: `error`, `warning`, `info`, `debug`.

### Async / Concurrency
- Use `asyncio.run()` in background threads for download operations.
- Communicate progress from worker thread to GUI via `queue.Queue`.
- Never block the tkinter main loop — use `after()` for periodic polling.
- Use `httpx.AsyncClient` (from `bilibili_api`) for HTTP downloads.

### Project Structure
```
bl_downloader/
  __main__.py        # Entry point: python -m bl_downloader
  __init__.py
  app.py             # tkinter GUI application
  types.py           # Shared type definitions
  errors.py          # Custom exceptions
  services/
    __init__.py
    video_info.py    # Fetch video metadata from Bilibili API
    downloader.py    # Download logic with progress reporting
  utils/
    __init__.py
    ffmpeg.py        # FFmpeg merge helper
tests/
  conftest.py
  test_video_info.py
  test_downloader.py
```

### Testing
- Use `pytest` with plain `assert` statements.
- Mock Bilibili API responses with `pytest-httpx` or `unittest.mock`.
- Keep test files in `tests/` mirroring the source structure.
- Use `pytest.fixture` for reusable test setup.

### Git / Commit
- Follow conventional commits: `type(scope): message`.
- Types: `feat`, `fix`, `chore`, `refactor`, `test`, `docs`, `style`.
- Keep commits small and atomic.
