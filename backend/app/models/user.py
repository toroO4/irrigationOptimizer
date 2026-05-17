"""
ORM Model — User.

Represents system users (farmers, agronomists, admins) who
interact with the irrigation scheduling platform.
"""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.farm import Farm


class User(Base, UUIDMixin, TimestampMixin):
    """
    User account model.

    Attributes:
        username: Unique login name.
        email: Contact email address.
        full_name: Display name.
        role: User role (admin, agronomist, farmer).
        api_key: Optional API key for programmatic access.
        is_active: Whether the account is enabled.
        farms: List of farms owned by this user.
    """

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True,
        doc="Unique username for login",
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True,
        doc="User email address",
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        doc="Full display name",
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="farmer",
        doc="User role: admin, agronomist, farmer",
    )
    api_key: Mapped[Optional[str]] = mapped_column(
        String(64), unique=True, nullable=True,
        doc="API key for programmatic access",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        doc="Whether the account is active",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        doc="Additional notes or bio",
    )

    # ── Relationships ────────────────────────────────────────────────
    farms: Mapped[List["Farm"]] = relationship(
        "Farm", back_populates="owner", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
