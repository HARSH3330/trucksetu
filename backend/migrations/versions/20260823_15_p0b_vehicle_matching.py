"""P0B approved vehicles and auditable match decisions.

Revision ID: 20260823_15
Revises: 20260823_14
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260823_15"
down_revision: str | None = "20260823_14"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("driver_profiles", sa.Column("licence_expires_on", sa.Date()))
    op.create_table(
        "carrier_vehicles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("provider_id", sa.Uuid(), sa.ForeignKey("provider_profiles.id"), nullable=False),
        sa.Column("vehicle_category_id", sa.Uuid(), sa.ForeignKey("vehicle_categories.id"), nullable=False),
        sa.Column("registration_number", sa.String(30), nullable=False, unique=True),
        sa.Column("body_type", sa.String(30), nullable=False),
        sa.Column("maximum_payload_tonnes", sa.Numeric(10, 3), nullable=False),
        sa.Column("internal_length_m", sa.Numeric(7, 3), nullable=False),
        sa.Column("internal_width_m", sa.Numeric(7, 3), nullable=False),
        sa.Column("internal_height_m", sa.Numeric(7, 3), nullable=False),
        sa.Column("maximum_volume_m3", sa.Numeric(10, 3), nullable=False),
        sa.Column("permit_territories", sa.JSON(), nullable=False),
        sa.Column("service_areas", sa.JSON(), nullable=False),
        sa.Column("rc_expires_on", sa.Date(), nullable=False),
        sa.Column("insurance_expires_on", sa.Date(), nullable=False),
        sa.Column("fitness_expires_on", sa.Date(), nullable=False),
        sa.Column("pollution_expires_on", sa.Date(), nullable=False),
        sa.Column("permit_expires_on", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("review_reason", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_carrier_vehicle_provider_status", "carrier_vehicles", ["provider_id", "status"])
    op.create_index("ix_carrier_vehicles_provider_id", "carrier_vehicles", ["provider_id"])
    op.create_index("ix_carrier_vehicles_registration_number", "carrier_vehicles", ["registration_number"])
    op.create_index("ix_carrier_vehicles_status", "carrier_vehicles", ["status"])
    op.add_column("trips", sa.Column("carrier_vehicle_id", sa.Uuid(), sa.ForeignKey("carrier_vehicles.id")))
    op.create_index("ix_trips_carrier_vehicle_id", "trips", ["carrier_vehicle_id"])
    op.add_column("available_routes", sa.Column("carrier_vehicle_id", sa.Uuid(), sa.ForeignKey("carrier_vehicles.id")))
    op.create_index("ix_available_routes_carrier_vehicle_id", "available_routes", ["carrier_vehicle_id"])
    op.create_table(
        "shared_match_evaluations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("request_id", sa.Uuid(), sa.ForeignKey("transport_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("available_route_id", sa.Uuid(), sa.ForeignKey("available_routes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evaluated_by", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("eligible", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Numeric(6, 2), nullable=False),
        sa.Column("rejection_reasons", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.JSON(), nullable=False),
        sa.Column("route_metrics", sa.JSON(), nullable=False),
        sa.Column("economics", sa.JSON(), nullable=False),
        sa.Column("overridden", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("override_reason", sa.Text()),
        sa.Column("overridden_by", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_shared_match_request_eligible", "shared_match_evaluations", ["request_id", "eligible", "expires_at"])
    op.create_index("ix_shared_match_route_created", "shared_match_evaluations", ["available_route_id", "created_at"])
    op.add_column("capacity_reservations", sa.Column("match_evaluation_id", sa.Uuid(), sa.ForeignKey("shared_match_evaluations.id")))
    op.create_unique_constraint("uq_capacity_reservation_match", "capacity_reservations", ["match_evaluation_id"])


def downgrade() -> None:
    op.drop_constraint("uq_capacity_reservation_match", "capacity_reservations", type_="unique")
    op.drop_column("capacity_reservations", "match_evaluation_id")
    op.drop_table("shared_match_evaluations")
    op.drop_index("ix_available_routes_carrier_vehicle_id", table_name="available_routes")
    op.drop_column("available_routes", "carrier_vehicle_id")
    op.drop_index("ix_trips_carrier_vehicle_id", table_name="trips")
    op.drop_column("trips", "carrier_vehicle_id")
    op.drop_table("carrier_vehicles")
    op.drop_column("driver_profiles", "licence_expires_on")
