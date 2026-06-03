import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone


PASSWORD_ITERATIONS = 260_000
SESSION_DAYS = 14
SESSION_SECONDS = SESSION_DAYS * 24 * 60 * 60


def utc_now():
    return datetime.now(timezone.utc)


def iso_now():
    return utc_now().isoformat()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        scheme, iterations, salt_b64, digest_b64 = stored_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def session_expiry():
    return utc_now() + timedelta(days=SESSION_DAYS)


def mask_identifier(value: str, left: int = 4, right: int = 4) -> str:
    if len(value) <= left + right:
        return "*" * len(value)
    return f"{value[:left]}****{value[-right:]}"
