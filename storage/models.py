from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from storage.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(Text, nullable=False)
    display_name = Column(String(120), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    sessions = relationship("UserSession", cascade="all, delete-orphan", back_populates="user")
    integrations = relationship("Integration", cascade="all, delete-orphan", back_populates="user")
    trusted_contacts = relationship("TrustedContact", cascade="all, delete-orphan", back_populates="user")
    app_registrations = relationship("AppRegistration", cascade="all, delete-orphan", back_populates="user")


class UserSession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="sessions")


class Integration(Base):
    __tablename__ = "integrations"
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_integrations_user_provider"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(80), nullable=False)
    status = Column(String(40), nullable=False)
    secret_ref = Column(Text)
    masked_label = Column(String(120))
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="integrations")


class TrustedContact(Base):
    __tablename__ = "trusted_contacts"
    __table_args__ = (UniqueConstraint("user_id", "provider", "name", name="uq_contacts_user_provider_name"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(80), nullable=False)
    name = Column(String(120), nullable=False)
    phone_ciphertext = Column(Text, nullable=False)
    phone_masked = Column(String(40), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="trusted_contacts")


class AppRegistration(Base):
    __tablename__ = "app_registrations"
    __table_args__ = (UniqueConstraint("user_id", "app_name", name="uq_apps_user_name"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    app_name = Column(String(120), nullable=False)
    app_path = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="app_registrations")


class AssistantLog(Base):
    __tablename__ = "assistant_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    sender = Column(String(40), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(String(40), nullable=False, default="info")
    created_at = Column(DateTime(timezone=True), nullable=False)
