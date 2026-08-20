"""Phase 11 identity and session security.

Revision ID: 20260819_10
Revises: 20260819_09
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "20260819_10"
down_revision: str | None = "20260819_09"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("email", sa.String(254), nullable=False), sa.Column("mobile", sa.String(20)), sa.Column("full_name", sa.String(120), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("status", sa.String(20), nullable=False, server_default="active"), sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("mobile_verified", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"), sa.Column("locked_until", sa.DateTime(timezone=True)), sa.Column("last_login_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.UniqueConstraint("email"), sa.UniqueConstraint("mobile"))
    op.create_index("ix_users_email", "users", ["email"]); op.create_index("ix_users_mobile", "users", ["mobile"])
    op.create_table("user_roles", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("role", sa.String(30), nullable=False))
    op.create_index("uq_user_role", "user_roles", ["user_id", "role"], unique=True)
    op.create_table("refresh_sessions", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("jti", sa.String(36), nullable=False, unique=True), sa.Column("family_id", sa.String(36), nullable=False), sa.Column("token_hash", sa.String(64), nullable=False), sa.Column("user_agent", sa.String(300)), sa.Column("ip_address", sa.String(64)), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("revoked_at", sa.DateTime(timezone=True)), sa.Column("replaced_by_jti", sa.String(36)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index("ix_refresh_sessions_user_id", "refresh_sessions", ["user_id"]); op.create_index("ix_refresh_sessions_family_id", "refresh_sessions", ["family_id"])
    op.create_table("account_verifications", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("channel", sa.String(20), nullable=False), sa.Column("code_hash", sa.String(255), nullable=False), sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("used_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index("ix_account_verifications_user_id", "account_verifications", ["user_id"])


def downgrade() -> None:
    op.drop_table("account_verifications"); op.drop_table("refresh_sessions"); op.drop_table("user_roles"); op.drop_table("users")
