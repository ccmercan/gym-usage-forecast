"""Add workout_duration_minutes

Revision ID: 002_add_workout_duration
Revises: 001_initial
Create Date: 2025-01-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_add_workout_duration'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add workout_duration_minutes column with default value
    op.add_column('user_preferences', 
        sa.Column('workout_duration_minutes', sa.Integer(), nullable=True, server_default='60')
    )
    # Update any existing rows to have default value
    op.execute("UPDATE user_preferences SET workout_duration_minutes = 60 WHERE workout_duration_minutes IS NULL")


def downgrade() -> None:
    op.drop_column('user_preferences', 'workout_duration_minutes')
