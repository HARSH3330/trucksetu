"""Phase 14 per-parcel loading and unloading rates.

Revision ID: 20260823_13
Revises: 20260823_12
"""
from collections.abc import Sequence
import json
from alembic import op

revision: str = "20260823_13"
down_revision: str | None = "20260823_12"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

NEW_RULE = {"minimum_fare":"2500","per_km_rate":"50","loading_base_charge":"100","loading_per_parcel":"7","unloading_base_charge":"100","unloading_per_parcel":"7","included_stops":2,"extra_stop_charge":"500","night_charge":"500","free_waiting_hours":"1","waiting_charge_per_hour":"500","range_percent":"10"}


def upgrade() -> None:
    encoded = json.dumps(NEW_RULE).replace("'", "''")
    op.execute(f"UPDATE application_settings SET value = '{encoded}'::json WHERE key = 'trip_price_suggestion'")


def downgrade() -> None:
    old = {**NEW_RULE, "loading_charge":"500", "unloading_charge":"500"}
    for key in ("loading_base_charge", "loading_per_parcel", "unloading_base_charge", "unloading_per_parcel"): old.pop(key)
    encoded = json.dumps(old).replace("'", "''")
    op.execute(f"UPDATE application_settings SET value = '{encoded}'::json WHERE key = 'trip_price_suggestion'")
