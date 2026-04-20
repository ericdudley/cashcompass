from __future__ import annotations

from uuid import uuid4


def generate_uid(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"
