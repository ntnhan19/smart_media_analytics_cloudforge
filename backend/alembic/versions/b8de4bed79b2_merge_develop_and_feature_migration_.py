"""merge develop and feature migration heads

Revision ID: b8de4bed79b2
Revises: 621d8f347414, 6d505627b4a2
Create Date: 2026-06-23 09:40:25.712346

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8de4bed79b2'
down_revision: Union[str, None] = ('621d8f347414', '6d505627b4a2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
