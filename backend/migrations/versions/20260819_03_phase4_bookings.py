"""Phase 4 bookings, allocation, trips, and OTPs.

Revision ID: 20260819_03
Revises: 20260819_02
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "20260819_03"
down_revision: str | None = "20260819_02"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table("driver_profiles", sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("provider_id",sa.Uuid(),sa.ForeignKey("provider_profiles.id"),nullable=False),sa.Column("full_name",sa.String(150),nullable=False),sa.Column("masked_mobile",sa.String(20),nullable=False),sa.Column("licence_number",sa.String(50),nullable=False,unique=True),sa.Column("kyc_status",sa.String(30),nullable=False,server_default="registered"),sa.Column("active",sa.Boolean(),nullable=False,server_default=sa.true()))
    op.create_index("ix_driver_profiles_provider_id","driver_profiles",["provider_id"])
    op.create_table("bookings",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("public_id",sa.String(30),nullable=False,unique=True),sa.Column("request_id",sa.Uuid(),sa.ForeignKey("transport_requests.id"),nullable=False),sa.Column("customer_id",sa.Uuid(),nullable=False),sa.Column("status",sa.String(30),nullable=False,server_default="advance_pending"),sa.Column("total_amount",sa.Numeric(14,2),nullable=False),sa.Column("currency",sa.String(3),nullable=False,server_default="INR"),sa.Column("customer_snapshot",sa.JSON(),nullable=False),sa.Column("route_snapshot",sa.JSON(),nullable=False),sa.Column("cargo_snapshot",sa.JSON(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.CheckConstraint("total_amount > 0",name="ck_booking_total"))
    op.create_index("ix_bookings_public_id","bookings",["public_id"]);op.create_index("ix_bookings_request_id","bookings",["request_id"]);op.create_index("ix_bookings_customer_id","bookings",["customer_id"])
    op.create_table("booking_allocations",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("booking_id",sa.Uuid(),sa.ForeignKey("bookings.id",ondelete="CASCADE"),nullable=False),sa.Column("quote_id",sa.Uuid(),sa.ForeignKey("quotes.id"),nullable=False),sa.Column("provider_id",sa.Uuid(),sa.ForeignKey("provider_profiles.id"),nullable=False),sa.Column("trucks_allocated",sa.Integer(),nullable=False),sa.Column("agreed_amount",sa.Numeric(14,2),nullable=False),sa.Column("quote_snapshot",sa.JSON(),nullable=False),sa.UniqueConstraint("booking_id","quote_id",name="uq_booking_quote_allocation"),sa.CheckConstraint("trucks_allocated > 0",name="ck_allocation_trucks"),sa.CheckConstraint("agreed_amount > 0",name="ck_allocation_amount"))
    op.create_table("trips",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("allocation_id",sa.Uuid(),sa.ForeignKey("booking_allocations.id",ondelete="CASCADE"),nullable=False),sa.Column("driver_id",sa.Uuid(),sa.ForeignKey("driver_profiles.id")),sa.Column("vehicle_registration",sa.String(30)),sa.Column("status",sa.String(40),nullable=False,server_default="booking_confirmed"),sa.Column("last_updated_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_index("ix_trips_allocation_id","trips",["allocation_id"])
    op.create_table("trip_status_history",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("trip_id",sa.Uuid(),sa.ForeignKey("trips.id",ondelete="CASCADE"),nullable=False),sa.Column("status",sa.String(40),nullable=False),sa.Column("changed_by",sa.Uuid(),nullable=False),sa.Column("notes",sa.Text()),sa.Column("location_text",sa.String(250)),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_index("ix_trip_status_history_trip_id","trip_status_history",["trip_id"])
    op.create_table("trip_otps",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("trip_id",sa.Uuid(),sa.ForeignKey("trips.id",ondelete="CASCADE"),nullable=False),sa.Column("otp_type",sa.String(20),nullable=False),sa.Column("otp_hash",sa.String(255),nullable=False),sa.Column("expires_at",sa.DateTime(timezone=True),nullable=False),sa.Column("attempts",sa.Integer(),nullable=False,server_default="0"),sa.Column("verified_at",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.CheckConstraint("otp_type IN ('pickup','delivery')",name="ck_trip_otp_type"),sa.CheckConstraint("attempts >= 0",name="ck_trip_otp_attempts"))
    op.create_index("ix_trip_otp_active","trip_otps",["trip_id","otp_type","verified_at"])


def downgrade() -> None:
    op.drop_table("trip_otps");op.drop_table("trip_status_history");op.drop_table("trips");op.drop_table("booking_allocations");op.drop_table("bookings");op.drop_index("ix_driver_profiles_provider_id",table_name="driver_profiles");op.drop_table("driver_profiles")
