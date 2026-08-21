"""Add ui_settings to users

Revision ID: 901ae777f0b3
Revises: 
Create Date: 2026-08-11 13:22:08.059374

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '901ae777f0b3'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('ui_settings', sa.JSON(), nullable=True, comment='Kullanıcıya özel arayüz ayarları (JSON)'))

def downgrade() -> None:
    op.drop_column('users', 'ui_settings')

