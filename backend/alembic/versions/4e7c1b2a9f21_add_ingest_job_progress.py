"""add ingest job progress

Revision ID: 4e7c1b2a9f21
Revises: 8ddd86ffa633
Create Date: 2026-06-19 15:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4e7c1b2a9f21"
down_revision: Union[str, None] = "8ddd86ffa633"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ingest_jobs",
        sa.Column("progress", sa.Float(), nullable=True, server_default="0"),
    )
    op.execute("UPDATE ingest_jobs SET progress = 0 WHERE progress IS NULL")


def downgrade() -> None:
    op.drop_column("ingest_jobs", "progress")
