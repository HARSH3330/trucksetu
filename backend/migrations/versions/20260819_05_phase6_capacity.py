"""Phase 6 available routes and capacity reservations.

Revision ID: 20260819_05
Revises: 20260819_04
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
revision: str="20260819_05";down_revision: str|None="20260819_04";branch_labels: Sequence[str]|None=None;depends_on: Sequence[str]|None=None


def upgrade() -> None:
    op.create_table("available_routes",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("provider_id",sa.Uuid(),sa.ForeignKey("provider_profiles.id"),nullable=False),sa.Column("vehicle_category_id",sa.Uuid(),sa.ForeignKey("vehicle_categories.id"),nullable=False),sa.Column("driver_id",sa.Uuid(),sa.ForeignKey("driver_profiles.id")),sa.Column("vehicle_registration",sa.String(30),nullable=False),sa.Column("origin_address",sa.Text(),nullable=False),sa.Column("origin_city",sa.String(100),nullable=False),sa.Column("destination_address",sa.Text(),nullable=False),sa.Column("destination_city",sa.String(100),nullable=False),sa.Column("ordered_route_cities",sa.JSON(),nullable=False),sa.Column("departure_at",sa.DateTime(timezone=True),nullable=False),sa.Column("total_capacity_tonnes",sa.Numeric(10,3),nullable=False),sa.Column("remaining_capacity_tonnes",sa.Numeric(10,3),nullable=False),sa.Column("minimum_booking_tonnes",sa.Numeric(10,3),nullable=False),sa.Column("allowed_cargo_types",sa.JSON(),nullable=False),sa.Column("price_amount",sa.Numeric(14,2),nullable=False),sa.Column("price_basis",sa.String(30),nullable=False),sa.Column("notes",sa.Text()),sa.Column("status",sa.String(20),nullable=False,server_default="active"),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.CheckConstraint("total_capacity_tonnes > 0",name="ck_route_total_capacity"),sa.CheckConstraint("remaining_capacity_tonnes >= 0 AND remaining_capacity_tonnes <= total_capacity_tonnes",name="ck_route_remaining_capacity"),sa.CheckConstraint("minimum_booking_tonnes > 0",name="ck_route_minimum_capacity"),sa.CheckConstraint("price_amount > 0",name="ck_route_price"),sa.CheckConstraint("price_basis IN ('per_tonne','per_kg','complete_capacity','negotiated')",name="ck_route_price_basis"))
    op.create_index("ix_available_routes_provider_id","available_routes",["provider_id"]);op.create_index("ix_available_routes_search","available_routes",["origin_city","destination_city","departure_at","status"])
    op.create_table("capacity_reservations",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("available_route_id",sa.Uuid(),sa.ForeignKey("available_routes.id"),nullable=False),sa.Column("customer_id",sa.Uuid(),nullable=False),sa.Column("cargo_type",sa.String(100),nullable=False),sa.Column("weight_tonnes",sa.Numeric(10,3),nullable=False),sa.Column("agreed_amount",sa.Numeric(14,2),nullable=False),sa.Column("status",sa.String(30),nullable=False,server_default="reserved"),sa.Column("idempotency_key",sa.String(100),nullable=False,unique=True),sa.Column("expires_at",sa.DateTime(timezone=True),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.CheckConstraint("weight_tonnes > 0",name="ck_capacity_reservation_weight"),sa.CheckConstraint("agreed_amount > 0",name="ck_capacity_reservation_amount"))
    op.create_index("ix_capacity_reservations_customer_id","capacity_reservations",["customer_id"]);op.create_index("ix_capacity_reservations_route_status","capacity_reservations",["available_route_id","status"])


def downgrade() -> None:
    op.drop_table("capacity_reservations");op.drop_table("available_routes")
