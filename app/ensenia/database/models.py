"""SQLAlchemy models for Ensenia chat system.

Models:
- Session: Chat sessions with metadata and research context
- Message: Individual messages in conversations
"""

from datetime import UTC, datetime

from sqlalchemy import ForeignKey, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""


class Session(Base):
    """Chat session model.

    Represents a conversation session with a student, including
    the mode (learn/practice/evaluation/study), grade level,
    subject, and optional research context from Cloudflare.
    """

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    grade: Mapped[int] = mapped_column(nullable=False)
    subject: Mapped[str] = mapped_column(nullable=False)
    mode: Mapped[str] = mapped_column(nullable=False)  # learn/practice/evaluation/study
    research_context: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship to messages
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """Return string representation of Session."""
        return (
            f"<Session(id={self.id}, mode={self.mode}, "
            f"grade={self.grade}, subject={self.subject})>"
        )


class Message(Base):
    """Message model.

    Represents an individual message in a conversation,
    from either the user or the assistant.
    """

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(nullable=False)  # user or assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), nullable=False
    )

    # Relationship to session
    session: Mapped["Session"] = relationship("Session", back_populates="messages")

    def __repr__(self) -> str:
        """Return string representation of Message."""
        return (
            f"<Message(id={self.id}, session_id={self.session_id}, "
            f"role={self.role}, timestamp={self.timestamp})>"
        )
