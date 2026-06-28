# This module provides transport-neutral HMAC signing and verification helpers.
import hashlib
import hmac
from typing import Union


SIGNATURE_HEADER = "X-HMAC-Signature"


def _normalize_hmac_body(body: Union[str, bytes]) -> bytes:
    # Normalize a request body into bytes before HMAC generation.
    if isinstance(body, bytes):
        return body
    return body.encode("utf-8")


def generate_hmac(body: Union[str, bytes], secret: str) -> str:
    # Generate a SHA-256 HMAC hex digest for the raw request body.
    normalized_body = _normalize_hmac_body(body)
    mac = hmac.new(secret.encode(encoding="utf-8"), normalized_body, hashlib.sha256)
    return mac.hexdigest()


def normalize_hmac_signature(signature: str) -> str:
    # Strip supported signature prefixes before verification.
    normalized_signature = (signature or "").strip().lower()
    for prefix in ("sha=", "sha256="):
        if normalized_signature.startswith(prefix):
            return normalized_signature[len(prefix):]
    return normalized_signature


def verify_hmac(body: bytes, sig: str, secret: str) -> bool:
    # Compare the provided signature with the expected HMAC signature.
    expected = generate_hmac(body, secret)
    normalized_signature = normalize_hmac_signature(sig)
    return hmac.compare_digest(expected, normalized_signature)
