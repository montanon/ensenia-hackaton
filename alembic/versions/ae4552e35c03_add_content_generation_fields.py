"""Add content generation fields to sessions table

Revision ID: ae4552e35c03
Revises: ae4552e35c02
Create Date: 2025-10-26 10:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ae4552e35c03"
down_revision: Union[str, None] = "ae4552e35c02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add learning_content and study_guide JSON columns to sessions table."""
    # Add JSON columns for generated content
    op.add_column(
        "sessions",
        sa.Column(
            "learning_content",
            postgresql.JSON(),
            nullable=True,
        ),
    )
    op.add_column(
        "sessions",
        sa.Column(
            "study_guide",
            postgresql.JSON(),
            nullable=True,
        ),
    )

    # Create indexes for checking content availability
    op.create_index(
        "idx_sessions_learning_content_exists",
        "sessions",
        [sa.literal_column("(learning_content IS NOT NULL)")],
        unique=False,
    )
    op.create_index(
        "idx_sessions_study_guide_exists",
        "sessions",
        [sa.literal_column("(study_guide IS NOT NULL)")],
        unique=False,
    )


def downgrade() -> None:
    """Remove learning_content and study_guide columns from sessions table."""
    # Drop indexes
    op.drop_index("idx_sessions_study_guide_exists", table_name="sessions")
    op.drop_index("idx_sessions_learning_content_exists", table_name="sessions")

    # Drop columns
    op.drop_column("sessions", "study_guide")
    op.drop_column("sessions", "learning_content")
