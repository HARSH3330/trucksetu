"""Phase 13 advisory route pricing.

Revision ID: 20260823_12
Revises: 20260819_11
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "20260823_12"
down_revision: str | None = "20260819_11"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table("trip_price_estimates", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("request_id", sa.Uuid(), sa.ForeignKey("transport_requests.id", ondelete="SET NULL")), sa.Column("pickup_text", sa.String(500), nullable=False), sa.Column("destination_text", sa.String(500), nullable=False), sa.Column("stop_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("distance_km", sa.Numeric(10, 2), nullable=False), sa.Column("duration_minutes", sa.Integer(), nullable=False), sa.Column("route_polyline", sa.Text()), sa.Column("rule_snapshot", sa.JSON(), nullable=False), sa.Column("breakdown", sa.JSON(), nullable=False), sa.Column("suggested_low", sa.Numeric(14, 2), nullable=False), sa.Column("suggested_high", sa.Numeric(14, 2), nullable=False), sa.Column("currency", sa.String(3), nullable=False, server_default="INR"), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index("ix_trip_price_estimates_request_id", "trip_price_estimates", ["request_id"])
    settings_table = sa.table("application_settings", sa.column("key", sa.String()), sa.column("value", sa.JSON()))
    op.bulk_insert(settings_table, [{"key": "trip_price_suggestion", "value": {"minimum_fare":"2500","per_km_rate":"50","loading_base_charge":"100","loading_per_parcel":"7","unloading_base_charge":"100","unloading_per_parcel":"7","included_stops":2,"extra_stop_charge":"500","night_charge":"500","free_waiting_hours":"1","waiting_charge_per_hour":"500","range_percent":"10"}}])


def downgrade() -> None:
    op.execute("DELETE FROM application_settings WHERE key = 'trip_price_suggestion'")
    op.drop_table("trip_price_estimates")
