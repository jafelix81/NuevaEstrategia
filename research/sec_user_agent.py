"""Shared SEC User-Agent resolution for research-only collectors.

Prefer the repository Actions secret. The fallback is the already-used
project contact from the Form 144 capture pipeline; it is not a credential.
"""
from __future__ import annotations

import os


SEC_USER_AGENT_FALLBACK = "NuevaEstrategia quantitative research jose.felix@felixsarmiento.com"


def resolve_sec_user_agent() -> tuple[str, str]:
    secret = os.environ.get("SEC_USER_AGENT", "").strip()
    if (
        secret
        and "@" in secret
        and "example.com" not in secret.lower()
        and "example.org" not in secret.lower()
        and "your-email" not in secret.lower()
        and "placeholder" not in secret.lower()
    ):
        return secret, "repository_secret"
    fallback = SEC_USER_AGENT_FALLBACK.strip()
    if (
        not fallback
        or "@" not in fallback
        or "example.com" in fallback.lower()
        or "example.org" in fallback.lower()
        or "your-email" in fallback.lower()
        or "placeholder" in fallback.lower()
    ):
        raise RuntimeError("no_valid_sec_user_agent_or_shared_contact_fallback")
    return fallback, "shared_project_contact_fallback"
