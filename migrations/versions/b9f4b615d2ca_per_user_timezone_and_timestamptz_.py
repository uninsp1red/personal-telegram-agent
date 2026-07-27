"""per-user timezone and timestamptz reminders

Revision ID: b9f4b615d2ca
Revises: 6098d9fdf5c2
Create Date: 2026-07-27 12:03:01.599210

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9f4b615d2ca'
down_revision: Union[str, Sequence[str], None] = '6098d9fdf5c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("timezone", sa.String(), server_default="UTC", nullable=False),
    )
    # Reminders are stored in UTC; make the column timezone-aware (timestamptz).
    op.execute(
        "ALTER TABLE message_schedule "
        "ALTER COLUMN time_to_send TYPE timestamptz USING time_to_send AT TIME ZONE 'UTC'"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "ALTER TABLE message_schedule "
        "ALTER COLUMN time_to_send TYPE timestamp USING time_to_send AT TIME ZONE 'UTC'"
    )
    op.drop_column("users", "timezone")
