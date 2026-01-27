"""Add last_alert_sent_date

Revision ID: 003_add_last_alert_date
Revises: 002_add_workout_duration
Create Date: 2025-01-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_add_last_alert_date'
down_revision: Union[str, None] = '002_add_workout_duration'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_preferences', 
        sa.Column('last_alert_sent_date', sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('user_preferences', 'last_alert_sent_date')
