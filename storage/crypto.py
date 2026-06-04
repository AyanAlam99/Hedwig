from cryptography.fernet import Fernet, InvalidToken

from storage.secrets import get_secret, set_secret


CONTACT_PHONE_KEY_REF = "app:contact_phone_encryption_key"


def _get_contact_cipher():
    key = get_secret(CONTACT_PHONE_KEY_REF)
    if not key:
        key = Fernet.generate_key().decode("ascii")
        set_secret(CONTACT_PHONE_KEY_REF, key)
    return Fernet(key.encode("ascii"))


def normalize_phone(phone: str) -> str:
    return (
        phone.strip()
        .replace("+", "")
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )


def mask_phone(phone: str) -> str:
    digits = normalize_phone(phone)
    if len(digits) <= 4:
        return "*" * len(digits)
    if len(digits) <= 8:
        return f"{'*' * (len(digits) - 4)}{digits[-4:]}"
    return f"{digits[:2]}{'*' * (len(digits) - 6)}{digits[-4:]}"


def encrypt_phone(phone: str) -> str:
    normalized = normalize_phone(phone)
    return _get_contact_cipher().encrypt(normalized.encode("utf-8")).decode("ascii")


def decrypt_phone(phone_ciphertext: str) -> str | None:
    if not phone_ciphertext:
        return None
    try:
        return _get_contact_cipher().decrypt(phone_ciphertext.encode("ascii")).decode("utf-8")
    except InvalidToken:
        return None
