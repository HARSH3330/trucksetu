"""Capacity reservation database invariants.

Revision ID: 20260906_16
Revises: 20260823_15
"""
from collections.abc import Sequence

from alembic import op

revision: str = "20260906_16"
down_revision: str | None = "20260823_15"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint("ck_route_remaining_volume", "available_routes", "remaining_volume_m3 >= 0 AND remaining_volume_m3 <= total_volume_m3")
    # Legacy rows received volume_m3=0 when the column was introduced; new API
    # requests require positive volume, while this invariant remains upgrade-safe.
    op.create_check_constraint("ck_reservation_positive_capacity", "capacity_reservations", "weight_tonnes > 0 AND volume_m3 >= 0")
    op.create_check_constraint("ck_reservation_status", "capacity_reservations", "status IN ('reserved','confirmed','expired','released')")


def downgrade() -> None:
    op.drop_constraint("ck_reservation_status", "capacity_reservations", type_="check")
    op.drop_constraint("ck_reservation_positive_capacity", "capacity_reservations", type_="check")
    op.drop_constraint("ck_route_remaining_volume", "available_routes", type_="check")
