"""Phase 2 customer marketplace tables.

Revision ID: 20260819_01
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260819_01"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vehicle_categories",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("body_type", sa.String(30), nullable=False),
        sa.Column("min_capacity_tonnes", sa.Numeric(8, 3), nullable=False),
        sa.Column("max_capacity_tonnes", sa.Numeric(8, 3), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("max_capacity_tonnes >= min_capacity_tonnes", name="ck_vehicle_capacity_range"),
    )
    op.create_table(
        "transport_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("public_id", sa.String(30), nullable=False, unique=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("pickup_address", sa.Text(), nullable=False),
        sa.Column("pickup_city", sa.String(100), nullable=False),
        sa.Column("destination_address", sa.Text(), nullable=False),
        sa.Column("destination_city", sa.String(100), nullable=False),
        sa.Column("pickup_date", sa.Date(), nullable=False),
        sa.Column("pickup_time", sa.String(10)),
        sa.Column("flexible_schedule", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("vehicle_category_id", sa.Uuid(), sa.ForeignKey("vehicle_categories.id")),
        sa.Column("vehicle_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("budget_amount", sa.Numeric(14, 2)),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("special_instructions", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("vehicle_count > 0", name="ck_request_vehicle_count"),
        sa.CheckConstraint("budget_amount IS NULL OR budget_amount > 0", name="ck_request_budget"),
    )
    op.create_index("ix_transport_requests_customer_id", "transport_requests", ["customer_id"])
    op.create_index("ix_transport_requests_public_id", "transport_requests", ["public_id"])
    op.create_index("ix_transport_requests_marketplace", "transport_requests", ["status", "pickup_date"])
    op.create_index("ix_transport_requests_route", "transport_requests", ["pickup_city", "destination_city"])
    op.create_table(
        "request_stops",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("request_id", sa.Uuid(), sa.ForeignKey("transport_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("activity", sa.String(30)),
        sa.Column("instructions", sa.Text()),
        sa.Column("contact_name", sa.String(100)),
        sa.UniqueConstraint("request_id", "position", name="uq_request_stop_position"),
    )
    op.create_table(
        "cargo_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("request_id", sa.Uuid(), sa.ForeignKey("transport_requests.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("weight_tonnes", sa.Numeric(10, 3), nullable=False),
        sa.Column("packages", sa.Integer()),
        sa.Column("fragile", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("perishable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("hazardous", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("temperature_controlled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("loading_assistance", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("unloading_assistance", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.CheckConstraint("weight_tonnes > 0", name="ck_cargo_positive_weight"),
    )


def downgrade() -> None:
    op.drop_table("cargo_items")
    op.drop_table("request_stops")
    op.drop_index("ix_transport_requests_route", table_name="transport_requests")
    op.drop_index("ix_transport_requests_marketplace", table_name="transport_requests")
    op.drop_index("ix_transport_requests_public_id", table_name="transport_requests")
    op.drop_index("ix_transport_requests_customer_id", table_name="transport_requests")
    op.drop_table("transport_requests")
    op.drop_table("vehicle_categories")
