from __future__ import annotations

import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger('safevixai.provider_encrypt')

_SALT = b'safevixai-provider-key-salt-v1'
_ITERATIONS = 600_000


def _derive_key(master_key: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(master_key.encode()))


def encrypt_api_key(api_key: str, master_key: str | None = None) -> str | None:
    if not api_key:
        return None
    key = master_key or os.getenv('PROVIDER_ENCRYPTION_KEY', '')
    if not key:
        logger.warning("PROVIDER_ENCRYPTION_KEY not set — storing API key in plaintext")
        return api_key
    try:
        f = Fernet(_derive_key(key))
        return f.encrypt(api_key.encode()).decode()
    except Exception as e:
        logger.error("Failed to encrypt API key: %s", e)
        return api_key


def decrypt_api_key(encrypted: str | None, master_key: str | None = None) -> str | None:
    if not encrypted:
        return None
    key = master_key or os.getenv('PROVIDER_ENCRYPTION_KEY', '')
    if not key:
        return encrypted
    try:
        f = Fernet(_derive_key(key))
        return f.decrypt(encrypted.encode()).decode()
    except Exception:
        return encrypted


def mask_api_key(api_key: str | None) -> str | None:
    if not api_key or len(api_key) < 8:
        return api_key
    return api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
