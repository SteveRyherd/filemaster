"""Simple encryption utilities using Fernet."""

from cryptography.fernet import Fernet


def generate_key() -> bytes:
    """Generate a new encryption key."""
    return Fernet.generate_key()


def encrypt(value: str, key: bytes) -> bytes:
    """Encrypt a string value."""
    return Fernet(key).encrypt(value.encode())


def decrypt(token: bytes, key: bytes) -> str:
    """Decrypt an encrypted value."""
    return Fernet(key).decrypt(token).decode()
