"""add module data fields

Revision ID: 09a08d6fa0c2
Revises: 3fe570611070
Create Date: 2025-06-07 20:35:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '09a08d6fa0c2'
down_revision = '3fe570611070'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('module', sa.Column('file_path', sa.String(length=255), nullable=True))
    op.add_column('module', sa.Column('answer', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('module', 'answer')
    op.drop_column('module', 'file_path')
