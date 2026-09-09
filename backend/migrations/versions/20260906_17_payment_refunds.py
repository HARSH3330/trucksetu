"""Auditable manual refunds for the closed pilot.

Revision ID: 20260906_17
Revises: 20260906_16
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260906_17"
down_revision: str | None = "20260906_16"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table("payment_refunds", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("booking_id", sa.Uuid(), sa.ForeignKey("bookings.id"), nullable=False), sa.Column("amount", sa.Numeric(14, 2), nullable=False), sa.Column("method", sa.String(30), nullable=False), sa.Column("reference", sa.String(100), nullable=False), sa.Column("idempotency_key", sa.String(100), nullable=False, unique=True), sa.Column("status", sa.String(30), nullable=False, server_default="processed"), sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.CheckConstraint("amount > 0", name="ck_payment_refund_amount"))
    op.create_index("ix_payment_refunds_booking_id", "payment_refunds", ["booking_id"])


def downgrade() -> None:
    op.drop_table("payment_refunds")
