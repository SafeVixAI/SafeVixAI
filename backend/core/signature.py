# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""GPG digital signature verification for update artifacts."""

from __future__ import annotations

import base64
import logging
import tempfile

logger = logging.getLogger("safevixai.backend.signature")


def verify_gpg_signature(
    artifact_path: str,
    signature_b64: str,
    public_key: str,
) -> dict:
    """Verify a base64-encoded GPG detached signature against an artifact.

    Args:
        artifact_path: Path or URL to the downloaded artifact.
        signature_b64: Base64-encoded GPG detached signature.
        public_key: ASCII-armored GPG public key block.

    Returns:
        dict with keys: valid (bool), fingerprint (str|None),
        status (str), error (str|None).
    """
    if not signature_b64:
        return {"valid": False, "fingerprint": None, "status": "no_signature", "error": "No signature provided"}
    if not public_key:
        return {"valid": False, "fingerprint": None, "status": "no_key", "error": "No public key configured"}

    try:
        import gnupg  # type: ignore[import-untyped]
    except ImportError:
        return {"valid": False, "fingerprint": None, "status": "unavailable", "error": "GPG module (python-gnupg) not installed"}

    try:
        with tempfile.NamedTemporaryFile(suffix=".asc", delete=False, mode="w") as sig_file:
            sig_data = base64.b64decode(signature_b64).decode("utf-8", errors="replace")
            sig_file.write(sig_data)
            sig_path = sig_file.name

        gpg = gnupg.GPG()
        import_result = gpg.import_keys(public_key)
        if import_result.count == 0:
            return {"valid": False, "fingerprint": None, "status": "invalid_key", "error": "Could not import public key"}

        with open(artifact_path, "rb") as artifact_fh:
            verified = gpg.verify_file(artifact_fh, sig_path)

        fingerprint = getattr(verified, "fingerprint", None) if verified else None
        return {
            "valid": bool(verified),
            "fingerprint": fingerprint,
            "status": "verified" if verified else "invalid",
            "error": None if verified else "Signature does not match",
        }
    except Exception as exc:
        logger.warning("GPG signature verification failed: %s", exc)
        return {"valid": False, "fingerprint": None, "status": "error", "error": str(exc)}
