"""add result_data json column

Revision ID: a1b2c3d4e5f6
Revises: 232fd1c975ea
Create Date: 2025-06-07 22:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '232fd1c975ea'
branch_labels = None
depends_on = None


def upgrade():
    # Check if result_data column already exists
    connection = op.get_bind()
    
    # Query to check if column exists
    result = connection.execute(text("PRAGMA table_info(module)"))
    columns = [row[1] for row in result.fetchall()]
    
    if 'result_data' not in columns:
        # Add the new JSON column only if it doesn't exist
        op.add_column('module', sa.Column('result_data', sa.JSON(), nullable=True))
    
    # Migrate existing data (only if result_data is NULL)
    # Migrate file_path data
    connection.execute(
        text("UPDATE module SET result_data = json_object('file_path', file_path, 'original_filename', file_path) "
             "WHERE file_path IS NOT NULL AND result_data IS NULL")
    )

    # Migrate answer data
    connection.execute(
        text("UPDATE module SET result_data = json_object('answer', answer) "
             "WHERE answer IS NOT NULL AND result_data IS NULL")
    )


def downgrade():
    op.drop_column('module', 'result_data')
