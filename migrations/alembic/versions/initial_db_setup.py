"""initial_db_setup

Revision ID: initial_db_setup
Revises: 
Create Date: 2023-03-25 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'initial_db_setup'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Создание таблицы users
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.VARCHAR(255), nullable=False),
        sa.Column('confirmed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('confiration_code', sa.String(), nullable=True),
        sa.Column('refresh_token', sa.String(), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
    )

    # Создание таблицы analysis
    op.create_table(
        'analysis',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('timestamp', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('analysis_id', UUID(as_uuid=True), nullable=False, unique=True),
    )

    # Создание таблицы results
    op.create_table(
        'results',
        sa.Column('analysis_id', UUID(as_uuid=True), sa.ForeignKey('analysis.analysis_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('file_activity', sa.String(), nullable=True),
        sa.Column('docker_output', sa.String(), nullable=True),
        sa.Column('results', sa.String(), nullable=True),
    )


def downgrade():
    # Удаление таблиц в обратном порядке
    op.drop_table('results')
    op.drop_table('analysis')
    op.drop_table('users') 