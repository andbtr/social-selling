"""update comments table

Revision ID: 05656722da5c
Revises: 56900ae8f390
Create Date: 2025-10-22 10:56:56.920354
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
# from sqlalchemy.dialects import postgresql  # evita usar tipos específicos en SQLite

# revision identifiers, used by Alembic.
revision: str = "05656722da5c"
down_revision: Union[str, None] = "56900ae8f390"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---- helpers ---------------------------------------------------------------
def _insp():
    return sa.inspect(op.get_bind())

def _table_exists(name: str) -> bool:
    return name in _insp().get_table_names()

def _index_exists(table: str, index_name: str) -> bool:
    try:
        return any(ix["name"] == index_name for ix in _insp().get_indexes(table))
    except Exception:
        return False

def _column_exists(table: str, column: str) -> bool:
    return any(c["name"] == column for c in _insp().get_columns(table))
# ----------------------------------------------------------------------------


def upgrade() -> None:
    # Evita dropear índices/tabla que puedan no existir en una BD limpia
    if _table_exists("posts"):
        for ix in ("ix_posts_id", "ix_posts_platform", "ix_posts_platform_id"):
            if _index_exists("posts", ix):
                op.drop_index(ix, table_name="posts")
        op.drop_table("posts")

    # Añade columnas en comments de forma idempotente
    if not _column_exists("comments", "intention_analized"):
        op.add_column("comments", sa.Column("intention_analized", sa.Boolean(), nullable=True))
    if not _column_exists("comments", "intention_analized_at"):
        op.add_column("comments", sa.Column("intention_analized_at", sa.DateTime(timezone=True), nullable=True))
    if not _column_exists("comments", "intention"):
        op.add_column("comments", sa.Column("intention", sa.String(length=5), nullable=True))
    if not _column_exists("comments", "intention_confidence"):
        op.add_column("comments", sa.Column("intention_confidence", sa.Float(), nullable=True))


def downgrade() -> None:
    # Quita columnas si existen (defensivo)
    if _column_exists("comments", "intention_confidence"):
        op.drop_column("comments", "intention_confidence")
    if _column_exists("comments", "intention"):
        op.drop_column("comments", "intention")
    if _column_exists("comments", "intention_analized_at"):
        op.drop_column("comments", "intention_analized_at")
    if _column_exists("comments", "intention_analized"):
        op.drop_column("comments", "intention_analized")

    if not _table_exists("posts"):
        op.create_table(
            "posts",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column("platform", sa.String(length=32), nullable=False),
            sa.Column("platform_id", sa.String(length=255), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("media_type", sa.String(), nullable=True),
            sa.Column("media_url", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("platform_created_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_posts_platform_id", "posts", ["platform_id"], unique=True)
        op.create_index("ix_posts_platform", "posts", ["platform"], unique=False)
        op.create_index("ix_posts_id", "posts", ["id"], unique=False)
