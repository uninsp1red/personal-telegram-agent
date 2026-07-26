"""add pgvector embedding to conversation_history

Revision ID: 6098d9fdf5c2
Revises: e63e33529673
Create Date: 2026-07-26 21:12:19.483707

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6098d9fdf5c2'
down_revision: Union[str, Sequence[str], None] = 'e63e33529673'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Voyage 3.5-lite embeddings are 1024-dimensional.
EMBEDDING_DIM = 1024


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        f"ALTER TABLE conversation_history ADD COLUMN embedding vector({EMBEDDING_DIM})"
    )
    # HNSW index for approximate nearest-neighbour search using cosine distance.
    op.execute(
        "CREATE INDEX ix_conversation_history_embedding "
        "ON conversation_history USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_conversation_history_embedding")
    op.execute("ALTER TABLE conversation_history DROP COLUMN IF EXISTS embedding")
    # Extension is left in place; other objects may depend on it.
