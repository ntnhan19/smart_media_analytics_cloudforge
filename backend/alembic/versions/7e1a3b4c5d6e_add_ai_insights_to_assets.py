# -*- coding: utf-8 -*-
"""add ai insights to assets

Revision ID: 7e1a3b4c5d6e
Revises: 6d505627b4a2
Create Date: 2026-06-22 16:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers của Alembic
revision: str = '7e1a3b4c5d6e'
down_revision: Union[str, None] = '6d505627b4a2'  # 🟢 Kế thừa trực tiếp từ file của thành viên khác
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Thêm các cột insights còn thiếu vào bảng assets ###
    op.add_column('assets', sa.Column('summary', sa.Text(), nullable=True))
    op.add_column('assets', sa.Column('moods', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('assets', sa.Column('objects', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('assets', sa.Column('best_for', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### Xóa các cột insights nếu có lệnh hạ cấp (rollback) ###
    op.drop_column('assets', 'best_for')
    op.drop_column('assets', 'objects')
    op.drop_column('assets', 'moods')
    op.drop_column('assets', 'summary')
    # ### end Alembic commands ###