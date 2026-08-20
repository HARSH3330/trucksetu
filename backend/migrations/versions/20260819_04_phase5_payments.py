"""Phase 5 payments, commissions, settings, and invoices.

Revision ID: 20260819_04
Revises: 20260819_03
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
revision: str="20260819_04";down_revision: str|None="20260819_03";branch_labels: Sequence[str]|None=None;depends_on: Sequence[str]|None=None


def upgrade() -> None:
    op.create_table("application_settings",sa.Column("key",sa.String(100),primary_key=True),sa.Column("value",sa.JSON(),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_table("payments",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("booking_id",sa.Uuid(),sa.ForeignKey("bookings.id"),nullable=False),sa.Column("payment_type",sa.String(20),nullable=False),sa.Column("provider",sa.String(30),nullable=False),sa.Column("gateway_order_id",sa.String(100),unique=True),sa.Column("gateway_payment_id",sa.String(100),unique=True),sa.Column("amount",sa.Numeric(14,2),nullable=False),sa.Column("currency",sa.String(3),nullable=False,server_default="INR"),sa.Column("method",sa.String(30)),sa.Column("status",sa.String(30),nullable=False,server_default="pending"),sa.Column("idempotency_key",sa.String(100),nullable=False,unique=True),sa.Column("metadata_json",sa.JSON(),nullable=False),sa.Column("confirmed_by",sa.Uuid()),sa.Column("paid_at",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.CheckConstraint("amount > 0",name="ck_payment_amount"),sa.CheckConstraint("payment_type IN ('advance','balance')",name="ck_payment_type"))
    op.create_index("ix_payments_booking_status","payments",["booking_id","status"])
    op.create_table("payment_events",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("payment_id",sa.Uuid(),sa.ForeignKey("payments.id",ondelete="CASCADE"),nullable=False),sa.Column("event_type",sa.String(100),nullable=False),sa.Column("gateway_event_id",sa.String(100),unique=True),sa.Column("payload",sa.JSON(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_index("ix_payment_events_payment_id","payment_events",["payment_id"])
    op.create_table("commissions",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("booking_id",sa.Uuid(),sa.ForeignKey("bookings.id"),nullable=False,unique=True),sa.Column("gross_amount",sa.Numeric(14,2),nullable=False),sa.Column("commission_percent",sa.Numeric(6,3),nullable=False),sa.Column("platform_commission",sa.Numeric(14,2),nullable=False),sa.Column("tax_amount",sa.Numeric(14,2),nullable=False),sa.Column("provider_payable",sa.Numeric(14,2),nullable=False),sa.Column("status",sa.String(30),nullable=False,server_default="pending_delivery"))
    op.create_table("invoices",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("booking_id",sa.Uuid(),sa.ForeignKey("bookings.id"),nullable=False,unique=True),sa.Column("invoice_number",sa.String(50),nullable=False,unique=True),sa.Column("legal_name",sa.String(200),nullable=False),sa.Column("gstin",sa.String(15)),sa.Column("billing_address",sa.Text(),nullable=False),sa.Column("taxable_amount",sa.Numeric(14,2),nullable=False),sa.Column("tax_percent",sa.Numeric(6,3),nullable=False),sa.Column("tax_amount",sa.Numeric(14,2),nullable=False),sa.Column("total_amount",sa.Numeric(14,2),nullable=False),sa.Column("status",sa.String(20),nullable=False,server_default="draft"),sa.Column("issued_at",sa.DateTime(timezone=True)),sa.Column("file_key",sa.String(500)))


def downgrade() -> None:
    op.drop_table("invoices");op.drop_table("commissions");op.drop_table("payment_events");op.drop_table("payments");op.drop_table("application_settings")
