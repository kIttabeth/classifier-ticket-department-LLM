# This module provides HMAC helpers and request verification middleware.
import hashlib
import hmac
from typing import Union

from fastapi import HTTPException, Request, status

from app.core.config import settings


SIGNATURE_HEADER = "X-HMAC-Signature"


def _normalize_hmac_body(body: Union[str, bytes]) -> bytes:
    # Normalize a request body into bytes before HMAC generation.
    if isinstance(body, bytes):
        return body
    return body.encode("utf-8")


def generate_hmac(body: Union[str, bytes], secret: str) -> str:
    # Generate a SHA-256 HMAC hex digest for the raw request body.
    normalized_body = _normalize_hmac_body(body)
    mac = hmac.new(secret.encode(), normalized_body, hashlib.sha256)
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


async def verify_request_hmac(request: Request, secret: str) -> None:
    # Validate the incoming request signature from the configured header.
    if request.method == "OPTIONS":
        return

    signature = request.headers.get(SIGNATURE_HEADER)
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing {SIGNATURE_HEADER} header",
        )

    body = await request.body()
    if not verify_hmac(body=body, sig=signature, secret=secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid request signature",
        )


async def verify_request_hmac_dependency(request: Request) -> None:
    # Verify HMAC for routes that opt in through router dependencies.
    await verify_request_hmac(request=request, secret=settings.SECRET_API_KEY)
