import secrets
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

TOKEN_FILE = Path.home() / '.gitflow' / '.api_token'


def _ensure_dir():
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)


def generate_token() -> str:
    _ensure_dir()
    token = secrets.token_hex(32)
    TOKEN_FILE.write_text(token)
    logger.info(f"Generated new API token: {token[:8]}...")
    return token


def get_token() -> str:
    _ensure_dir()
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    return generate_token()


def verify_token(token: str) -> bool:
    if not token:
        return False
    saved = get_token()
    return secrets.compare_digest(token, saved)


def revoke_token() -> None:
    _ensure_dir()
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
    logger.info("API token revoked")
