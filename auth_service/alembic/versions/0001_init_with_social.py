"""init with social_accounts

Revision ID: 0001_init_with_social
Revises:
Create Date: 2025-09-27

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '0001_init_with_social'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- roles ---
    op.create_table(
        'roles',
        sa.Column('role_id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # --- users ---
    op.create_table(
        'users',
        sa.Column('user_id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # --- login_history ---
    op.create_table(
        'login_history',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.user_id', ondelete="CASCADE"), nullable=False),
        sa.Column('user_agent', sa.String(length=255)),
        sa.Column('ip_address', sa.String(length=50)),
        sa.Column('login_time', sa.DateTime(), nullable=False),
    )

    # --- user_roles ---
    op.create_table(
        'user_roles',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.user_id', ondelete="CASCADE"), nullable=False),
        sa.Column('role_id', sa.UUID(), sa.ForeignKey('roles.role_id', ondelete="CASCADE"), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
    )

    # --- social_accounts ---
    op.create_table(
        'social_accounts',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.user_id', ondelete="CASCADE"), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('provider_account_id', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("provider", "provider_account_id", name="uq_provider_account"),
    )


def downgrade() -> None:
    op.drop_table('social_accounts')
    op.drop_table('user_roles')
    op.drop_table('login_history')
    op.drop_table('users')
    op.drop_table('roles')
