"""Phase 3 provider marketplace and quotations.

Revision ID: 20260819_02
Revises: 20260819_01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260819_02"
down_revision: str | None = "20260819_01"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "provider_profiles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("display_name", sa.String(150), nullable=False),
        sa.Column("kyc_status", sa.String(30), nullable=False, server_default="registered"),
        sa.Column("rating", sa.Numeric(3, 2), nullable=False, server_default="0"),
        sa.Column("completed_trips", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cancellation_percent", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint("rating >= 0 AND rating <= 5", name="ck_provider_rating"),
        sa.CheckConstraint("cancellation_percent >= 0 AND cancellation_percent <= 100", name="ck_provider_cancellation"),
    )
    op.create_index("ix_provider_profiles_kyc_status", "provider_profiles", ["kyc_status"])
    op.create_table(
        "quotes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("request_id", sa.Uuid(), sa.ForeignKey("transport_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_id", sa.Uuid(), sa.ForeignKey("provider_profiles.id"), nullable=False),
        sa.Column("vehicle_category_id", sa.Uuid(), sa.ForeignKey("vehicle_categories.id"), nullable=False),
        sa.Column("final_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("vehicles_offered", sa.Integer(), nullable=False),
        sa.Column("estimated_pickup", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estimated_delivery", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text()), sa.Column("inclusions", sa.Text()), sa.Column("exclusions", sa.Text()),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("final_price > 0", name="ck_quote_price"),
        sa.CheckConstraint("vehicles_offered > 0", name="ck_quote_vehicle_count"),
        sa.UniqueConstraint("request_id", "provider_id", name="uq_active_provider_request_quote"),
    )
    op.create_index("ix_quotes_request_price", "quotes", ["request_id", "status", "final_price"])
    op.create_table(
        "quote_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("quote_id", sa.Uuid(), sa.ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("final_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("vehicles_offered", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("quote_id", "version", name="uq_quote_version"),
    )
    op.create_table(
        "negotiations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("quote_id", sa.Uuid(), sa.ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_role", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("amount > 0", name="ck_negotiation_amount"),
        sa.CheckConstraint("sender_role IN ('customer', 'provider')", name="ck_negotiation_sender"),
    )
    op.create_index("ix_negotiations_quote_created", "negotiations", ["quote_id", "created_at"])


def downgrade() -> None:
    op.drop_table("negotiations")
    op.drop_table("quote_versions")
    op.drop_table("quotes")
    op.drop_index("ix_provider_profiles_kyc_status", table_name="provider_profiles")
    op.drop_table("provider_profiles")
