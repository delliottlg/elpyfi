from fastapi import Header, HTTPException
import secrets
from .config import settings


VALID_API_KEYS = set(settings.api_keys.split(",")) if settings.api_keys else set()


async def verify_api_key(x_api_key: str = Header(None)):
    if not VALID_API_KEYS:
        # No auth in dev mode
        return True

    if not x_api_key or x_api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True


def generate_api_key() -> str:
    """Generate a new API key"""
    return f"elpyfi_{secrets.token_urlsafe(32)}"
