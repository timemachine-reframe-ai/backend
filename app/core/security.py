"""Password hashing helpers."""
import base64
import hashlib
import hmac
import os
from typing import Tuple

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 390000
SALT_SIZE = 16


def _b64encode(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"))


def _split_hash(stored_hash: str) -> Tuple[str, int, bytes, bytes]:
    algo, iter_str, salt_b64, hash_b64 = stored_hash.split("$")
    return algo, int(iter_str), _b64decode(salt_b64), _b64decode(hash_b64)


def hash_password(plain_password: str) -> str:
    """Generate a salted PBKDF2 hash for the given password."""
    if not plain_password:
        raise ValueError("Password must not be empty")
    salt = os.urandom(SALT_SIZE)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt,
        ITERATIONS,
    )
    return f"{ALGORITHM}${ITERATIONS}${_b64encode(salt)}${_b64encode(dk)}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Verify a password against the stored hash."""
    try:
        algo, iterations, salt, hash_bytes = _split_hash(stored_hash)
    except ValueError:
        return False
    if algo != ALGORITHM:
        return False
    computed = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(computed, hash_bytes)
