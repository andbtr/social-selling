"""update comments

Revision ID: 56900ae8f390
Revises:
Create Date: 2025-10-16 02:21:08.590121
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
# from sqlalchemy.dialects import postgresql  # (solo si vas a recrear 'posts' en downgrade)

# revision identifiers, used by Alembic.
revision: str = "56900ae8f390"
down_revision: Union[str, None] = None
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
    # --- Drop índices/tabla 'posts' solo si existen (BD limpia no los tendrá) ---
    if _table_exists("posts"):
        for ix in ("ix_posts_id", "ix_posts_platform", "ix_posts_platform_id"):
            if _index_exists("posts", ix):
                op.drop_index(ix, table_name="posts")
        op.drop_table("posts")

    # --- Nuevas columnas en 'comments' (agregar solo si no existen) ---
    if not _column_exists("comments", "sentiment_analized"):
        op.add_column("comments", sa.Column("sentiment_analized", sa.Boolean(), nullable=True))
    if not _column_exists("comments", "sentiment_analized_at"):
        op.add_column("comments", sa.Column("sentiment_analized_at", sa.DateTime(timezone=True), nullable=True))
    if not _column_exists("comments", "sentiment"):
        op.add_column("comments", sa.Column("sentiment", sa.String(length=5), nullable=True))
    if not _column_exists("comments", "sentiment_confidence"):
        op.add_column("comments", sa.Column("sentiment_confidence", sa.Float(), nullable=True))


def downgrade() -> None:
    # --- Quitar columnas si existen (defensivo) ---
    if _column_exists("comments", "sentiment_confidence"):
        op.drop_column("comments", "sentiment_confidence")
    if _column_exists("comments", "sentiment"):
        op.drop_column("comments", "sentiment")
    if _column_exists("comments", "sentiment_analized_at"):
        op.drop_column("comments", "sentiment_analized_at")
    if _column_exists("comments", "sentiment_analized"):
        op.drop_column("comments", "sentiment_analized")

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
