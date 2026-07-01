from __future__ import annotations

import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

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
    return kdf.derive(master_key.encode())


def encrypt_api_key(api_key: str, master_key: str | None = None) -> str | None:
    if not api_key:
        return None
    key = master_key or os.getenv('PROVIDER_ENCRYPTION_KEY', '')
    if not key:
        logger.warning("PROVIDER_ENCRYPTION_KEY not set — storing API key in plaintext")
        return api_key
    try:
        derived_key = _derive_key(key)
        aesgcm = AESGCM(derived_key)
        nonce = os.urandom(12)
        ct = aesgcm.encrypt(nonce, api_key.encode('utf-8'), None)
        # Prefix with v2_ to distinguish from Fernet easily
        return "v2_" + base64.urlsafe_b64encode(nonce + ct).decode('utf-8')
    except Exception as e:
        logger.error("Failed to encrypt API key: %s", e)
        return api_key


def decrypt_api_key(encrypted: str | None, master_key: str | None = None) -> str | None:
    if not encrypted:
        return None
    key = master_key or os.getenv('PROVIDER_ENCRYPTION_KEY', '')
    if not key:
        return encrypted

    derived_key = _derive_key(key)
    
    if encrypted.startswith("v2_"):
        try:
            data = base64.urlsafe_b64decode(encrypted[3:].encode('utf-8'))
            nonce, ct = data[:12], data[12:]
            aesgcm = AESGCM(derived_key)
            return aesgcm.decrypt(nonce, ct, None).decode('utf-8')
        except Exception:
            return encrypted
    
    # Fallback to Fernet
    try:
        f = Fernet(base64.urlsafe_b64encode(derived_key))
        return f.decrypt(encrypted.encode('utf-8')).decode('utf-8')
    except Exception:
        return encrypted


def mask_api_key(api_key: str | None) -> str | None:
    if not api_key or len(api_key) < 8:
        return api_key
    return api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
