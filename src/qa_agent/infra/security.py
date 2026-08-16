"""Security module: keyring-based secret storage + encrypted config fallback."""

import json
import os
from pathlib import Path

from ..infra.logging import logger

_SECRET_FILE = Path.home() / ".qa_agent" / "secrets.json"


def _ensure_dir():
    _SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_secrets() -> dict:
    if _SECRET_FILE.exists():
        try:
            return json.loads(_SECRET_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_secrets(secrets: dict):
    _ensure_dir()
    _SECRET_FILE.write_text(json.dumps(secrets, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(_SECRET_FILE, 0o600)


def store_secret(key: str, value: str):
    """Store a secret (API key) by key name."""
    try:
        import keyring as kr
        kr.set_password("qa_agent", key, value)
        logger.debug("Secret stored in keyring: %s", key)
    except Exception:
        secrets = _load_secrets()
        secrets[key] = value
        _save_secrets(secrets)
        logger.debug("Secret stored in file: %s", key)


def load_secret(key: str) -> str:
    """Load a secret by key name."""
    if not key:
        return ""
    try:
        import keyring as kr
        val = kr.get_password("qa_agent", key)
        if val:
            return val
    except Exception:
        pass
    secrets = _load_secrets()
    return secrets.get(key, "")


def delete_secret(key: str):
    """Delete a secret."""
    try:
        import keyring as kr
        kr.delete_password("qa_agent", key)
    except Exception:
        pass
    secrets = _load_secrets()
    secrets.pop(key, None)
    _save_secrets(secrets)
