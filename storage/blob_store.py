from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from storage.database import get_db
from storage.models import ParkedBlob
from storage.security import utc_now

_DEFAULT_TTL_HOURS = 48


def park_blob(user_id: int, provider: str, ciphertext_b64: str, ttl_hours: int = _DEFAULT_TTL_HOURS) -> int:
    now = utc_now()
    blob = ParkedBlob(
        user_id=user_id,
        provider=provider,
        ciphertext_b64=ciphertext_b64,
        created_at=now,
        expires_at=now + timedelta(hours=ttl_hours),
    )
    with get_db() as db:
        db.add(blob)
        db.flush()
        return blob.id


def get_pending_blobs(user_id: int) -> list[dict]:
    now = datetime.now(timezone.utc)
    with get_db() as db:
        blobs = db.execute(
            select(ParkedBlob)
            .where(ParkedBlob.user_id == user_id, ParkedBlob.expires_at > now)
            .order_by(ParkedBlob.created_at)
        ).scalars().all()
        return [
            {
                "id": b.id,
                "provider": b.provider,
                "ciphertext_b64": b.ciphertext_b64,
                "expires_at": b.expires_at,
            }
            for b in blobs
        ]


def delete_blob(blob_id: int, user_id: int):
    """Deletes a blob after it has been successfully applied."""
    with get_db() as db:
        db.execute(
            delete(ParkedBlob).where(
                ParkedBlob.id == blob_id,
                ParkedBlob.user_id == user_id,
            )
        )


def purge_expired():
    """Removes all expired blobs across all users. Call on startup."""
    now = datetime.now(timezone.utc)
    with get_db() as db:
        db.execute(delete(ParkedBlob).where(ParkedBlob.expires_at <= now))
