from __future__ import annotations

import json
import logging
from pathlib import Path

from bilibili_api import Credential

logger = logging.getLogger(__name__)


def _get_credential_dir() -> Path:
    return Path.home() / ".bl_downloader"


def _get_credential_path() -> Path:
    return _get_credential_dir() / "credential.json"


def _credential_to_dict(credential: Credential) -> dict[str, str]:
    keys = ["sessdata", "bili_jct", "buvid3", "buvid4", "dedeuserid", "ac_time_value"]
    return {k: v for k in keys if (v := getattr(credential, k, None)) is not None}


def save_credential(credential: Credential) -> None:
    path = _get_credential_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _credential_to_dict(credential)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Credential saved to %s", path)


def load_credential() -> Credential | None:
    path = _get_credential_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Credential(**data)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Failed to load credential: %s", e)
        return None


def delete_credential() -> None:
    path = _get_credential_path()
    if path.exists():
        path.unlink()
        logger.info("Credential deleted from %s", path)
