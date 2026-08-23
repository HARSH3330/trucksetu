"""P0A booking modes, shipment dimensions, time windows and route volume.

Revision ID: 20260823_14
Revises: 20260823_13
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260823_14"
down_revision: str | None = "20260823_13"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    for name in ("internal_length_m", "internal_width_m", "internal_height_m"):
        op.add_column("vehicle_categories", sa.Column(name, sa.Numeric(7, 3), nullable=True))
    op.add_column("vehicle_categories", sa.Column("max_volume_m3", sa.Numeric(10, 3), nullable=True))

    op.add_column("transport_requests", sa.Column("booking_mode", sa.String(30), nullable=False, server_default="FULL_VEHICLE"))
    op.add_column("transport_requests", sa.Column("schedule_mode", sa.String(20), nullable=False, server_default="SCHEDULED"))
    op.add_column("transport_requests", sa.Column("earliest_pickup_at", sa.DateTime(timezone=True)))
    op.add_column("transport_requests", sa.Column("latest_pickup_at", sa.DateTime(timezone=True)))
    op.add_column("transport_requests", sa.Column("delivery_deadline_at", sa.DateTime(timezone=True)))
    op.add_column("transport_requests", sa.Column("maximum_added_time_minutes", sa.Integer()))
    op.create_index("ix_transport_requests_booking_mode", "transport_requests", ["booking_mode"])
    op.add_column("quotes", sa.Column("service_mode", sa.String(30), nullable=False, server_default="FULL_VEHICLE"))
    op.add_column("bookings", sa.Column("booking_mode", sa.String(30), nullable=False, server_default="FULL_VEHICLE"))
    op.add_column("bookings", sa.Column("schedule_mode", sa.String(20), nullable=False, server_default="SCHEDULED"))
    op.add_column("bookings", sa.Column("capacity_reservation_id", sa.Uuid()))
    op.create_unique_constraint("uq_booking_capacity_reservation", "bookings", ["capacity_reservation_id"])
    op.create_foreign_key("fk_booking_capacity_reservation", "bookings", "capacity_reservations", ["capacity_reservation_id"], ["id"])

    for name in ("length_m", "width_m", "height_m"):
        op.add_column("cargo_items", sa.Column(name, sa.Numeric(7, 3)))
    op.add_column("cargo_items", sa.Column("volume_m3", sa.Numeric(10, 3)))
    op.add_column("cargo_items", sa.Column("dimensions_are_per_package", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("cargo_items", sa.Column("high_value", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("cargo_items", sa.Column("stackable", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("cargo_items", sa.Column("pickup_floor", sa.Integer()))
    op.add_column("cargo_items", sa.Column("pickup_has_lift", sa.Boolean()))
    op.add_column("cargo_items", sa.Column("vehicle_body_requirement", sa.String(30)))
    op.add_column("cargo_items", sa.Column("delivery_instructions", sa.Text()))

    op.add_column("available_routes", sa.Column("departure_window_end", sa.DateTime(timezone=True)))
    op.add_column("available_routes", sa.Column("expected_arrival_at", sa.DateTime(timezone=True)))
    op.add_column("available_routes", sa.Column("route_geometry", sa.Text()))
    op.add_column("available_routes", sa.Column("repeat_schedule", sa.JSON()))
    op.add_column("available_routes", sa.Column("maximum_deviation_km", sa.Numeric(8, 2), nullable=False, server_default="0"))
    op.add_column("available_routes", sa.Column("maximum_added_time_minutes", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("available_routes", sa.Column("total_volume_m3", sa.Numeric(10, 3), nullable=False, server_default="0"))
    op.add_column("available_routes", sa.Column("remaining_volume_m3", sa.Numeric(10, 3), nullable=False, server_default="0"))
    op.add_column("available_routes", sa.Column("minimum_acceptable_earning", sa.Numeric(14, 2), nullable=False, server_default="0"))
    op.add_column("available_routes", sa.Column("service_areas", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("available_routes", sa.Column("permit_territories", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("capacity_reservations", sa.Column("volume_m3", sa.Numeric(10, 3), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_constraint("fk_booking_capacity_reservation", "bookings", type_="foreignkey")
    op.drop_constraint("uq_booking_capacity_reservation", "bookings", type_="unique")
    for name in ("capacity_reservation_id", "schedule_mode", "booking_mode"):
        op.drop_column("bookings", name)
    op.drop_column("quotes", "service_mode")
    op.drop_column("capacity_reservations", "volume_m3")
    for name in ("permit_territories", "service_areas", "minimum_acceptable_earning", "remaining_volume_m3", "total_volume_m3", "maximum_added_time_minutes", "maximum_deviation_km", "repeat_schedule", "route_geometry", "expected_arrival_at", "departure_window_end"):
        op.drop_column("available_routes", name)
    for name in ("delivery_instructions", "vehicle_body_requirement", "pickup_has_lift", "pickup_floor", "stackable", "high_value", "dimensions_are_per_package", "volume_m3", "height_m", "width_m", "length_m"):
        op.drop_column("cargo_items", name)
    op.drop_index("ix_transport_requests_booking_mode", table_name="transport_requests")
    for name in ("maximum_added_time_minutes", "delivery_deadline_at", "latest_pickup_at", "earliest_pickup_at", "schedule_mode", "booking_mode"):
        op.drop_column("transport_requests", name)
    for name in ("max_volume_m3", "internal_height_m", "internal_width_m", "internal_length_m"):
        op.drop_column("vehicle_categories", name)
