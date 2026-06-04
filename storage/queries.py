import json
from datetime import datetime, timezone

from sqlalchemy import delete, select

from storage.database import get_db
from storage.crypto import decrypt_phone, encrypt_phone, mask_phone, normalize_phone
from storage.models import Integration, TrustedContact, User, UserSession
from storage.security import hash_session_token, utc_now


def _user_to_dict(user: User | None):
    if not user:
        return None
    return {
        "id": user.id,
        "email": user.email,
        "password_hash": user.password_hash,
        "display_name": user.display_name,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


def _integration_to_dict(integration: Integration | None):
    if not integration:
        return None
    return {
        "id": integration.id,
        "user_id": integration.user_id,
        "provider": integration.provider,
        "status": integration.status,
        "secret_ref": integration.secret_ref,
        "masked_label": integration.masked_label,
        "metadata": json.loads(integration.metadata_json or "{}"),
        "created_at": integration.created_at,
        "updated_at": integration.updated_at,
    }


def create_user(email: str, password_hash: str, display_name: str):
    now = utc_now()
    user = User(
        email=email.lower().strip(),
        password_hash=password_hash,
        display_name=display_name.strip(),
        created_at=now,
        updated_at=now,
    )
    with get_db() as db:
        db.add(user)
        db.flush()
        return _user_to_dict(user)


def get_user_by_id(user_id: int):
    with get_db() as db:
        user = db.get(User, user_id)
        return _user_to_dict(user)


def get_user_by_email(email: str):
    with get_db() as db:
        user = db.execute(
            select(User).where(User.email == email.lower().strip())
        ).scalar_one_or_none()
        return _user_to_dict(user)


def public_user(user: dict):
    return {
        "id": user["id"],
        "email": user["email"],
        "display_name": user["display_name"],
    }


def create_session(user_id: int, token: str, expires_at):
    session = UserSession(
        user_id=user_id,
        token_hash=hash_session_token(token),
        expires_at=expires_at,
        created_at=utc_now(),
    )
    with get_db() as db:
        db.add(session)


def delete_session(token: str):
    with get_db() as db:
        db.execute(
            delete(UserSession).where(UserSession.token_hash == hash_session_token(token))
        )


def get_user_by_session_token(token: str):
    token_hash = hash_session_token(token)
    with get_db() as db:
        session = db.execute(
            select(UserSession).where(UserSession.token_hash == token_hash)
        ).scalar_one_or_none()

        if not session:
            return None

        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= datetime.now(timezone.utc):
            db.delete(session)
            return None

        return _user_to_dict(session.user)


def upsert_integration(
    user_id: int,
    provider: str,
    status: str,
    secret_ref: str | None,
    masked_label: str | None,
    metadata: dict | None = None,
):
    now = utc_now()
    with get_db() as db:
        integration = db.execute(
            select(Integration).where(
                Integration.user_id == user_id,
                Integration.provider == provider,
            )
        ).scalar_one_or_none()

        if not integration:
            integration = Integration(
                user_id=user_id,
                provider=provider,
                created_at=now,
            )
            db.add(integration)

        integration.status = status
        integration.secret_ref = secret_ref
        integration.masked_label = masked_label
        integration.metadata_json = json.dumps(metadata or {})
        integration.updated_at = now


def get_integration(user_id: int, provider: str):
    with get_db() as db:
        integration = db.execute(
            select(Integration).where(
                Integration.user_id == user_id,
                Integration.provider == provider,
            )
        ).scalar_one_or_none()
        return _integration_to_dict(integration)


def list_integrations(user_id: int):
    with get_db() as db:
        integrations = db.execute(
            select(Integration)
            .where(Integration.user_id == user_id)
            .order_by(Integration.provider)
        ).scalars().all()
        return [_integration_to_dict(item) for item in integrations]


def add_trusted_contact(user_id: int, provider: str, name: str, phone: str):
    now = utc_now()
    normalized_name = name.strip().lower()
    phone_clean = normalize_phone(phone)

    with get_db() as db:
        contact = db.execute(
            select(TrustedContact).where(
                TrustedContact.user_id == user_id,
                TrustedContact.provider == provider,
                TrustedContact.name == normalized_name,
            )
        ).scalar_one_or_none()

        if not contact:
            contact = TrustedContact(
                user_id=user_id,
                provider=provider,
                name=normalized_name,
                created_at=now,
            )
            db.add(contact)

        contact.phone = ""
        contact.phone_ciphertext = encrypt_phone(phone_clean)
        contact.phone_masked = mask_phone(phone_clean)
        contact.updated_at = now


def remove_trusted_contact(user_id: int, provider: str, name: str):
    with get_db() as db:
        db.execute(
            delete(TrustedContact).where(
                TrustedContact.user_id == user_id,
                TrustedContact.provider == provider,
                TrustedContact.name == name.strip().lower(),
            )
        )


def list_trusted_contacts(user_id: int, provider: str):
    with get_db() as db:
        contacts = db.execute(
            select(TrustedContact)
            .where(
                TrustedContact.user_id == user_id,
                TrustedContact.provider == provider,
            )
            .order_by(TrustedContact.name)
        ).scalars().all()
        return {
            contact.name: contact.phone_masked or mask_phone(contact.phone)
            for contact in contacts
        }


def list_trusted_contact_numbers(user_id: int, provider: str):
    with get_db() as db:
        contacts = db.execute(
            select(TrustedContact)
            .where(
                TrustedContact.user_id == user_id,
                TrustedContact.provider == provider,
            )
            .order_by(TrustedContact.name)
        ).scalars().all()

        numbers = {}
        for contact in contacts:
            phone = decrypt_phone(contact.phone_ciphertext) if contact.phone_ciphertext else contact.phone
            if phone:
                numbers[contact.name] = phone
        return numbers
