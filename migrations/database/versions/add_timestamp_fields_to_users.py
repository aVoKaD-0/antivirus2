"""add timestamp fields to users

Revision ID: add_timestamp_fields_to_users
Revises: 
Create Date: 2024-03-24 08:52:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_timestamp_fields_to_users'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Добавляем поля created_at и expires_at
    op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('users', sa.Column('expires_at', sa.DateTime(), nullable=True))

def downgrade():
    # Удаляем поля created_at и expires_at
    op.drop_column('users', 'expires_at')
    op.drop_column('users', 'created_at') 