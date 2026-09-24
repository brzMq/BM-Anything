"""initial schema: schema_meta bookkeeping table

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-24

P0 acceptance: "数据库迁移可从空库执行". This is the first migration; running
``alembic upgrade head`` against an empty SQLite file must create the
``schema_meta`` table and insert the BM identity row.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "schema_meta",
        sa.Column("key", sa.String(length=64), primary_key=True),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.execute(
        "INSERT INTO schema_meta (key, value) VALUES "
        "('bm_schema_version', '0.1.0'), "
        "('created_by', 'bm-anything/alembic')"
    )


def downgrade() -> None:
    op.drop_table("schema_meta")
