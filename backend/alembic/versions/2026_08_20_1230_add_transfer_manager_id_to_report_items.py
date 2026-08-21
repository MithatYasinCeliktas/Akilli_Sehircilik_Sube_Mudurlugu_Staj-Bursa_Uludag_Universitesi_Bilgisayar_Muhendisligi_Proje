'''add transfer_manager_id to report_items

Revision ID: 2026_08_20_1230_add_transfer_manager_id_to_report_items
Revises: 2026_08_20_0911-fb42b25680c6_add_lists_to_activity_reports
Create Date: 2026-08-20 12:30:00
'''

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260820_1230'
down_revision = 'fb42b25680c6'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('report_items', sa.Column('transfer_manager_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_report_items_transfer_manager_id_users',
        'report_items',
        'users',
        ['transfer_manager_id'],
        ['id'],
        ondelete='SET NULL'
    )

def downgrade():
    op.drop_constraint('fk_report_items_transfer_manager_id_users', 'report_items', type_='foreignkey')
    op.drop_column('report_items', 'transfer_manager_id')
