"""lead scoring tables

Revision ID: f5f7a811cfd7
Revises: 05656722da5c
Create Date: 2025-10-23 19:17:47.755933
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f5f7a811cfd7"
down_revision: Union[str, None] = "05656722da5c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---- helpers ---------------------------------------------------------------
def _inspector():
    return sa.inspect(op.get_bind())

def _table_exists(name: str) -> bool:
    insp = _inspector()
    return name in insp.get_table_names()

def _column_exists(table: str, column: str) -> bool:
    insp = _inspector()
    return any(c["name"] == column for c in insp.get_columns(table))

def _index_exists(table: str, index_name: str) -> bool:
    insp = _inspector()
    try:
        return any(ix["name"] == index_name for ix in insp.get_indexes(table))
    except Exception:
        # algunos dialectos pueden no soportar get_indexes
        return False
# ----------------------------------------------------------------------------


def upgrade() -> None:
    # --- lead_thresholds -----------------------------------------------------
    if not _table_exists("lead_thresholds"):
        op.create_table(
            "lead_thresholds",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("scoring_version", sa.Text(), nullable=False),
            sa.Column("alpha", sa.Numeric(precision=3, scale=2), nullable=False),
            sa.Column("beta", sa.Numeric(precision=3, scale=2), nullable=False),
            sa.Column("fkw_min", sa.Numeric(precision=3, scale=2), nullable=False),
            sa.Column("fkw_max", sa.Numeric(precision=3, scale=2), nullable=False),
            sa.Column("hot_min", sa.Numeric(precision=5, scale=2), nullable=False),
            sa.Column("warm_min", sa.Numeric(precision=5, scale=2), nullable=False),
            sa.Column("min_intent_for_hot", sa.Numeric(precision=3, scale=2), nullable=False),
            sa.Column("active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("lead_thresholds", "ix_lead_thresholds_id"):
        op.create_index(op.f("ix_lead_thresholds_id"), "lead_thresholds", ["id"], unique=False)

    # --- lead_scores ---------------------------------------------------------
    if not _table_exists("lead_scores"):
        op.create_table(
            "lead_scores",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("comment_id", sa.BigInteger(), nullable=False),
            sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=False),
            sa.Column("priority_level", sa.String(length=10), nullable=False),
            sa.Column("scoring_version", sa.Text(), nullable=False),
            sa.Column("computed_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["comment_id"], ["comments.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("lead_scores", "idx_lead_scores_priority"):
        op.create_index("idx_lead_scores_priority", "lead_scores", ["priority_level", "score"], unique=False)
    if not _index_exists("lead_scores", "idx_lead_scores_time"):
        op.create_index("idx_lead_scores_time", "lead_scores", ["computed_at"], unique=False)
    if not _index_exists("lead_scores", "ix_lead_scores_comment_id"):
        op.create_index(op.f("ix_lead_scores_comment_id"), "lead_scores", ["comment_id"], unique=False)
    if not _index_exists("lead_scores", "ix_lead_scores_id"):
        op.create_index(op.f("ix_lead_scores_id"), "lead_scores", ["id"], unique=False)

    # --- Nuevas columnas en comments ----------------------------------------
    if not _column_exists("comments", "sentiment_analized"):
        op.add_column("comments", sa.Column("sentiment_analized", sa.Boolean(), nullable=True))
    if not _column_exists("comments", "sentiment_analized_at"):
        op.add_column("comments", sa.Column("sentiment_analized_at", sa.DateTime(timezone=True), nullable=True))
    if not _column_exists("comments", "sentiment"):
        op.add_column("comments", sa.Column("sentiment", sa.String(length=5), nullable=True))
    if not _column_exists("comments", "sentiment_confidence"):
        op.add_column("comments", sa.Column("sentiment_confidence", sa.Float(), nullable=True))
    if not _column_exists("comments", "intention_analized"):
        op.add_column("comments", sa.Column("intention_analized", sa.Boolean(), nullable=True))
    if not _column_exists("comments", "intention_analized_at"):
        op.add_column("comments", sa.Column("intention_analized_at", sa.DateTime(timezone=True), nullable=True))
    if not _column_exists("comments", "intention"):
        op.add_column("comments", sa.Column("intention", sa.String(length=5), nullable=True))
    if not _column_exists("comments", "intention_confidence"):
        op.add_column("comments", sa.Column("intention_confidence", sa.Float(), nullable=True))

    # --- Cambio de tipo de comments.rating (SQLite-safe) ---------------------
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    # Solo intentamos si la columna existe
    if _column_exists("comments", "rating"):
        if is_sqlite:
            # recrea la tabla con batch para soportar ALTER TYPE en SQLite
            with op.batch_alter_table("comments", recreate="always") as batch_op:
                batch_op.alter_column(
                    "rating",
                    existing_type=sa.INTEGER(),
                    type_=sa.Float(),
                    existing_nullable=True,
                    nullable=True,
                )
        else:
            op.alter_column(
                "comments",
                "rating",
                existing_type=sa.INTEGER(),
                type_=sa.Float(),
                existing_nullable=True,
                nullable=True,
            )

    # --- Insertar umbrales por defecto --------------------------------------
    op.execute("""
        INSERT INTO lead_thresholds
        (scoring_version, alpha, beta, fkw_min, fkw_max, hot_min, warm_min, min_intent_for_hot, active, created_at)
        SELECT 'v1', 0.70, 0.30, 0.60, 1.60, 80.00, 60.00, 0.50, 1, CURRENT_TIMESTAMP
        WHERE NOT EXISTS (SELECT 1 FROM lead_thresholds WHERE active = 1);
        """)


def downgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    # revert rating type
    if _column_exists("comments", "rating"):
        if is_sqlite:
            with op.batch_alter_table("comments", recreate="always") as batch_op:
                batch_op.alter_column(
                    "rating",
                    existing_type=sa.Float(),
                    type_=sa.INTEGER(),
                    existing_nullable=True,
                    nullable=True,
                )
        else:
            op.alter_column(
                "comments",
                "rating",
                existing_type=sa.Float(),
                type_=sa.INTEGER(),
                existing_nullable=True,
                nullable=True,
            )

    # drop added columns (guarded)
    for col in [
        "intention_confidence",
        "intention",
        "intention_analized_at",
        "intention_analized",
        "sentiment_confidence",
        "sentiment",
        "sentiment_analized_at",
        "sentiment_analized",
    ]:
        if _column_exists("comments", col):
            op.drop_column("comments", col)

    # drop lead_scores
    if _table_exists("lead_scores"):
        if _index_exists("lead_scores", "ix_lead_scores_id"):
            op.drop_index(op.f("ix_lead_scores_id"), table_name="lead_scores")
        if _index_exists("lead_scores", "ix_lead_scores_comment_id"):
            op.drop_index(op.f("ix_lead_scores_comment_id"), table_name="lead_scores")
        if _index_exists("lead_scores", "idx_lead_scores_time"):
            op.drop_index("idx_lead_scores_time", table_name="lead_scores")
        if _index_exists("lead_scores", "idx_lead_scores_priority"):
            op.drop_index("idx_lead_scores_priority", table_name="lead_scores")
        op.drop_table("lead_scores")

    # drop lead_thresholds
    if _table_exists("lead_thresholds"):
        if _index_exists("lead_thresholds", "ix_lead_thresholds_id"):
            op.drop_index(op.f("ix_lead_thresholds_id"), table_name="lead_thresholds")
        op.drop_table("lead_thresholds")