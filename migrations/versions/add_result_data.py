"""add result_data json column

Revision ID: add_result_data
Revises: 51d4dc079555
Create Date: 2025-06-07 22:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Add the new JSON column
    op.add_column('module', sa.Column('result_data', sa.JSON(), nullable=True))

    # Migrate existing data
    connection = op.get_bind()

    # Migrate file_path data
    connection.execute(
        "UPDATE module SET result_data = json_object('file_path', file_path, 'original_filename', file_path) "
        "WHERE file_path IS NOT NULL"
    )

    # Migrate answer data
    connection.execute(
        "UPDATE module SET result_data = json_object('answer', answer) "
        "WHERE answer IS NOT NULL AND result_data IS NULL"
    )


def downgrade():
    op.drop_column('module', 'result_data')
