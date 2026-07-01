"""Google Chat webhook JWT authentication.

When MOCK_MODE=true, authentication is bypassed for local testing.
To enable real auth: set MOCK_MODE=false and provide GCHAT_PROJECT_NUMBER.
"""

import os
import logging
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

# ─── MOCK MODE TOGGLE ───────────────────────────────────────────────────────
# Set MOCK_MODE=false once real credentials are available
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

# Google Chat sends JWTs signed by this issuer
_CHAT_ISSUER = "chat@system.gserviceaccount.com"

# Your GCP project number (not project ID) — required for audience verification
_PROJECT_NUMBER = os.getenv("GCHAT_PROJECT_NUMBER", "")


async def verify_gchat_request(request: Request) -> None:
    """Verify that the incoming request is from Google Chat.

    Raises HTTPException(403) if verification fails.
    When MOCK_MODE is enabled, this is a no-op.
    """
    if MOCK_MODE:
        logger.debug("MOCK_MODE enabled — skipping Google Chat JWT verification")
        return

    # --- Real verification below ---
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Missing or invalid Authorization header")

    token = auth_header.removeprefix("Bearer ").strip()

    if not _PROJECT_NUMBER:
        logger.error("GCHAT_PROJECT_NUMBER not set — cannot verify audience")
        raise HTTPException(status_code=500, detail="Server misconfiguration: missing project number")

    expected_audience = _PROJECT_NUMBER

    try:
        claim = id_token.verify_token(
            token,
            google_requests.Request(),
            audience=expected_audience,
        )
        # Confirm issuer
        if claim.get("iss") != _CHAT_ISSUER:
            raise ValueError(f"Unexpected issuer: {claim.get('iss')}")

        logger.debug(f"Verified Google Chat request from: {claim.get('email')}")

    except Exception as e:
        logger.warning(f"Google Chat JWT verification failed: {e}")
        raise HTTPException(status_code=403, detail="Unauthorized: invalid token")
