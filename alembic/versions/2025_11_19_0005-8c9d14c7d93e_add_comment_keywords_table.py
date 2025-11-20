"""add comment_keywords table

Revision ID: 8c9d14c7d93e
Revises: dee39d8a80ba
Create Date: 2025-11-19 00:05:46.365252

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c9d14c7d93e'
down_revision: Union[str, None] = 'dee39d8a80ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'comment_keywords',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('comment_id', sa.Integer(), sa.ForeignKey('comments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('keyword', sa.String(128), nullable=False, index=True),
        sa.Column('frequency', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

def downgrade():
    op.drop_table('comment_keywords')
