"""Tamper-evident evidence utilities."""
import hashlib


def digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def verify(content: str, expected_sha256: str) -> bool:
    return digest(content) == expected_sha256.lower()
