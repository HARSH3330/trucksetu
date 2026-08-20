"""Phase 7 reviews, disputes, cancellations, and reports.

Revision ID: 20260819_06
Revises: 20260819_05
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
revision: str="20260819_06";down_revision: str|None="20260819_05";branch_labels: Sequence[str]|None=None;depends_on: Sequence[str]|None=None


def upgrade() -> None:
    op.create_table("reviews",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("booking_id",sa.Uuid(),sa.ForeignKey("bookings.id"),nullable=False),sa.Column("reviewer_id",sa.Uuid(),nullable=False),sa.Column("reviewer_role",sa.String(20),nullable=False),sa.Column("target_id",sa.Uuid(),nullable=False),sa.Column("target_role",sa.String(20),nullable=False),sa.Column("rating",sa.Integer(),nullable=False),sa.Column("comment",sa.Text()),sa.Column("tags",sa.JSON(),nullable=False),sa.Column("verified_trip",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.CheckConstraint("rating BETWEEN 1 AND 5",name="ck_review_rating"),sa.UniqueConstraint("booking_id","reviewer_id","target_id",name="uq_review_parties"))
    op.create_index("ix_reviews_target_id","reviews",["target_id"])
    op.create_table("disputes",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("booking_id",sa.Uuid(),sa.ForeignKey("bookings.id"),nullable=False),sa.Column("raised_by",sa.Uuid(),nullable=False),sa.Column("category",sa.String(50),nullable=False),sa.Column("description",sa.Text(),nullable=False),sa.Column("status",sa.String(30),nullable=False,server_default="open"),sa.Column("priority",sa.String(20),nullable=False,server_default="normal"),sa.Column("resolution",sa.Text()),sa.Column("resolved_by",sa.Uuid()),sa.Column("resolved_at",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_index("ix_disputes_booking_id","disputes",["booking_id"])
    op.create_table("dispute_messages",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("dispute_id",sa.Uuid(),sa.ForeignKey("disputes.id",ondelete="CASCADE"),nullable=False),sa.Column("sender_id",sa.Uuid(),nullable=False),sa.Column("message",sa.Text(),nullable=False),sa.Column("attachment_keys",sa.JSON(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_index("ix_dispute_messages_dispute_id","dispute_messages",["dispute_id"])
    op.create_table("cancellations",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("booking_id",sa.Uuid(),sa.ForeignKey("bookings.id"),nullable=False,unique=True),sa.Column("cancelled_by",sa.Uuid(),nullable=False),sa.Column("reason_code",sa.String(50),nullable=False),sa.Column("reason_detail",sa.Text()),sa.Column("booking_status_snapshot",sa.String(30),nullable=False),sa.Column("policy_snapshot",sa.JSON(),nullable=False),sa.Column("cancellation_fee",sa.Numeric(14,2),nullable=False),sa.Column("refund_amount",sa.Numeric(14,2),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.CheckConstraint("cancellation_fee >= 0 AND refund_amount >= 0",name="ck_cancellation_amounts"))
    op.create_table("safety_reports",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("reporter_id",sa.Uuid(),nullable=False),sa.Column("subject_user_id",sa.Uuid(),nullable=False),sa.Column("booking_id",sa.Uuid(),sa.ForeignKey("bookings.id")),sa.Column("category",sa.String(50),nullable=False),sa.Column("description",sa.Text(),nullable=False),sa.Column("status",sa.String(30),nullable=False,server_default="under_review"),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_index("ix_safety_reports_reporter_id","safety_reports",["reporter_id"]);op.create_index("ix_safety_reports_subject_user_id","safety_reports",["subject_user_id"])


def downgrade() -> None:
    op.drop_table("safety_reports");op.drop_table("cancellations");op.drop_table("dispute_messages");op.drop_table("disputes");op.drop_table("reviews")
