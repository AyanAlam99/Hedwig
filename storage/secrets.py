SERVICE_NAME = "hedwig"


class SecretStorageUnavailable(RuntimeError):
    pass


def _keyring():
    try:
        import keyring

    except ImportError as exc:
        
        raise SecretStorageUnavailable(
            "Secure secret storage is unavailable. Install the 'keyring' package."
        ) from exc
    return keyring


def make_secret_ref(user_id: int, provider: str, secret_name: str) -> str:
    return f"user:{user_id}:{provider}:{secret_name}"


def set_secret(secret_ref: str, value: str):
    _keyring().set_password(SERVICE_NAME, secret_ref, value)


def get_secret(secret_ref: str) -> str | None:
    return _keyring().get_password(SERVICE_NAME, secret_ref)


def delete_secret(secret_ref: str):
    try:
        _keyring().delete_password(SERVICE_NAME, secret_ref)
    except Exception:
        pass
