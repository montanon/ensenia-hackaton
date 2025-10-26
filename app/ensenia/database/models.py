"""SQLAlchemy models for Ensenia chat system.

Models:
- Session: Chat sessions with metadata and research context
- Message: Individual messages in conversations
- Exercise: Generated exercises for student practice
- ExerciseSession: Junction table linking exercises to sessions
- MinistryStandard: Chilean Ministry of Education learning objectives
- CurriculumContent: Educational content aligned with ministry standards
"""

from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class OutputMode(str, Enum):
    """Enum for message output modes."""

    TEXT = "text"
    AUDIO = "audio"


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
        server_default=func.now(), nullable=False, index=True
    )
    grade: Mapped[int] = mapped_column(nullable=False, index=True)
    subject: Mapped[str] = mapped_column(nullable=False, index=True)
    mode: Mapped[str] = mapped_column(
        nullable=False, index=True
    )  # learn/practice/evaluation/study
    research_context: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Generated content for Learn and Study pages
    learning_content: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # Structured learning materials from research
    study_guide: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # Study guide with key concepts and review materials

    # WebSocket and audio mode support
    current_mode: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default=OutputMode.TEXT.value,
        server_default=OutputMode.TEXT.value,
    )  # text or audio - current output mode preference
    ws_connection_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # WebSocket connection identifier

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
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(nullable=False, index=True)  # user or assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )

    # Audio support fields
    output_mode: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default=OutputMode.TEXT.value,
        server_default=OutputMode.TEXT.value,
    )  # How this message was delivered: text or audio
    audio_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )  # Reference to cached audio file (hash)
    audio_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )  # CDN/static URL for audio playback
    audio_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )  # TTS generation status
    audio_duration: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # Audio length in seconds

    # Relationship to session
    session: Mapped["Session"] = relationship("Session", back_populates="messages")

    def __repr__(self) -> str:
        """Return string representation of Message."""
        return (
            f"<Message(id={self.id}, session_id={self.session_id}, "
            f"role={self.role}, timestamp={self.timestamp})>"
        )


class Exercise(Base):
    """Exercise model.

    Represents a generated exercise for student practice.
    Supports multiple types (multiple_choice, true_false, short_answer, essay)
    with content stored as JSONB for flexibility.
    """

    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    exercise_type: Mapped[str] = mapped_column(
        nullable=False, index=True
    )  # multiple_choice, true_false, short_answer, essay
    grade: Mapped[int] = mapped_column(nullable=False, index=True)
    subject: Mapped[str] = mapped_column(nullable=False, index=True)
    topic: Mapped[str] = mapped_column(nullable=False, index=True)

    # Exercise content stored as JSONB for flexibility
    # Structure varies by type but always includes:
    # - question: str
    # - learning_objective: str (aligned with Chilean curriculum)
    # Type-specific fields in JSONB:
    #   multiple_choice: options, correct_answer, explanation
    #   true_false: correct_answer, explanation
    #   short_answer: rubric, example_answer
    #   essay: rubric, key_points, min_words, max_words
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Validation score from agent-validator loop (0-10)
    validation_score: Mapped[int] = mapped_column(Integer, nullable=False)

    # Difficulty level (1-5, where 1=easy, 5=advanced)
    difficulty_level: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Whether this exercise is public (can be reused for other students)
    is_public: Mapped[bool] = mapped_column(nullable=False, default=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False, index=True
    )

    # Relationship to exercise sessions (many-to-many through junction table)
    exercise_sessions: Mapped[list["ExerciseSession"]] = relationship(
        "ExerciseSession", back_populates="exercise", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Composite index for fast searches by curriculum alignment
        Index("idx_exercise_curriculum", "grade", "subject", "topic", "is_public"),
        # Index for difficulty-based filtering
        Index("idx_exercise_difficulty", "grade", "difficulty_level", "is_public"),
    )

    def __repr__(self) -> str:
        """Return string representation of Exercise."""
        return (
            f"<Exercise(id={self.id}, type={self.exercise_type}, "
            f"grade={self.grade}, subject={self.subject}, topic={self.topic})>"
        )


class ExerciseSession(Base):
    """ExerciseSession junction model.

    Links exercises to sessions, tracking which exercises
    were used in which student sessions.
    """

    __tablename__ = "exercise_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False, index=True
    )

    # Optional: student's answer and completion status
    student_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_completed: Mapped[bool] = mapped_column(nullable=False, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    exercise: Mapped["Exercise"] = relationship(
        "Exercise", back_populates="exercise_sessions"
    )
    session: Mapped["Session"] = relationship("Session")

    __table_args__ = (
        # Composite index for querying exercises by session
        Index("idx_exercise_session", "session_id", "assigned_at"),
        # Unique constraint to prevent duplicate assignments
        Index("idx_unique_exercise_session", "exercise_id", "session_id", unique=True),
    )

    def __repr__(self) -> str:
        """Return string representation of ExerciseSession."""
        return (
            f"<ExerciseSession(id={self.id}, exercise_id={self.exercise_id}, "
            f"session_id={self.session_id}, completed={self.is_completed})>"
        )


class MinistryStandard(Base):
    """Ministry Standard model.

    Represents Chilean Ministry of Education learning objectives (OAs).
    Used for curriculum alignment and validation.
    """

    __tablename__ = "ministry_standards"

    oa_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    grade: Mapped[int] = mapped_column(nullable=False, index=True)
    subject: Mapped[str] = mapped_column(nullable=False, index=True)
    oa_code: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    skills: Mapped[list] = mapped_column(JSONB, nullable=False)
    keywords: Mapped[str] = mapped_column(Text, nullable=False)
    official_document_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_ministry_grade_subject", "grade", "subject"),
        Index("idx_ministry_oa_code", "oa_code"),
    )

    def __repr__(self) -> str:
        """Return string representation of MinistryStandard."""
        return (
            f"<MinistryStandard(oa_id={self.oa_id}, grade={self.grade}, "
            f"subject={self.subject}, oa_code={self.oa_code})>"
        )


class CurriculumContent(Base):
    """Curriculum Content model.

    Represents educational content chunks aligned with ministry standards.
    Used for RAG retrieval and content generation.
    """

    __tablename__ = "curriculum_content"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    grade: Mapped[int] = mapped_column(nullable=False, index=True)
    subject: Mapped[str] = mapped_column(nullable=False, index=True)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    learning_objectives: Mapped[list] = mapped_column(
        JSONB, nullable=False
    )  # Array of OA IDs
    ministry_standard_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    ministry_approved: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )  # 0=pending, 1=approved
    keywords: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    difficulty_level: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # easy, medium, hard
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Additional metadata for RAG
    chunk_index: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=0, server_default="0"
    )
    source_file: Mapped[str | None] = mapped_column(String(500), nullable=True)
    embedding_generated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    __table_args__ = (
        Index("idx_curriculum_grade_subject", "grade", "subject"),
        Index("idx_curriculum_difficulty", "difficulty_level"),
        Index("idx_curriculum_embedding", "embedding_generated"),
    )

    def __repr__(self) -> str:
        """Return string representation of CurriculumContent."""
        return (
            f"<CurriculumContent(id={self.id}, title={self.title}, "
            f"grade={self.grade}, subject={self.subject})>"
        )
