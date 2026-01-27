"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if tables exist before creating (handles case where Base.metadata.create_all was used)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'usage_snapshots' not in existing_tables:
        op.create_table(
            'usage_snapshots',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('timestamp_utc', sa.DateTime(), nullable=False),
            sa.Column('location_name', sa.String(), nullable=False),
            sa.Column('usage_percentage', sa.Integer(), nullable=False),
            sa.Column('scraped_at_utc', sa.DateTime(), nullable=True),
            sa.Column('parser_version', sa.String(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_usage_snapshots_timestamp', 'usage_snapshots', ['timestamp_utc'])
        op.create_index('ix_usage_snapshots_location', 'usage_snapshots', ['location_name'])
    
    if 'user_preferences' not in existing_tables:
        op.create_table(
            'user_preferences',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(), nullable=False),
            sa.Column('timezone', sa.String(), nullable=True),
            sa.Column('preferred_start_time_local', sa.String(), nullable=True),
            sa.Column('preferred_end_time_local', sa.String(), nullable=True),
            sa.Column('preferred_days', postgresql.ARRAY(sa.Integer()), nullable=True),
            sa.Column('areas_of_interest', postgresql.ARRAY(sa.String()), nullable=True),
            sa.Column('crowd_tolerance_pct', sa.Integer(), nullable=True),
            sa.Column('digest_send_time_local', sa.String(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    op.drop_table('user_preferences')
    op.drop_index('ix_usage_snapshots_location', table_name='usage_snapshots')
    op.drop_index('ix_usage_snapshots_timestamp', table_name='usage_snapshots')
    op.drop_table('usage_snapshots')
