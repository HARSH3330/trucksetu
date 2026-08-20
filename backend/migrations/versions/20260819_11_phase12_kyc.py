"""Phase 12 provider KYC and private documents.

Revision ID: 20260819_11
Revises: 20260819_10
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "20260819_11"
down_revision: str | None = "20260819_10"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("provider_profiles", sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE")))
    op.add_column("provider_profiles", sa.Column("provider_type", sa.String(30), nullable=False, server_default="individual"))
    op.create_index("ix_provider_profiles_user_id", "provider_profiles", ["user_id"], unique=True)
    op.create_table("kyc_applications", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("provider_id", sa.Uuid(), sa.ForeignKey("provider_profiles.id", ondelete="CASCADE"), nullable=False), sa.Column("status", sa.String(30), nullable=False, server_default="registered"), sa.Column("legal_name", sa.String(160), nullable=False), sa.Column("pan_last_four", sa.String(4)), sa.Column("gstin", sa.String(15)), sa.Column("submitted_at", sa.DateTime(timezone=True)), sa.Column("reviewed_at", sa.DateTime(timezone=True)), sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("users.id")), sa.Column("decision_reason", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index("ix_kyc_applications_provider_id", "kyc_applications", ["provider_id"]); op.create_index("ix_kyc_applications_status", "kyc_applications", ["status"])
    op.create_table("kyc_documents", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("application_id", sa.Uuid(), sa.ForeignKey("kyc_applications.id", ondelete="CASCADE"), nullable=False), sa.Column("document_type", sa.String(50), nullable=False), sa.Column("storage_key", sa.String(500), nullable=False, unique=True), sa.Column("original_filename", sa.String(255), nullable=False), sa.Column("content_type", sa.String(100), nullable=False), sa.Column("size_bytes", sa.Integer(), nullable=False), sa.Column("expires_on", sa.Date()), sa.Column("status", sa.String(30), nullable=False, server_default="uploaded"), sa.Column("rejection_reason", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index("ix_kyc_document_application_type", "kyc_documents", ["application_id", "document_type"])
    op.create_table("kyc_review_events", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("application_id", sa.Uuid(), sa.ForeignKey("kyc_applications.id", ondelete="CASCADE"), nullable=False), sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False), sa.Column("previous_status", sa.String(30), nullable=False), sa.Column("new_status", sa.String(30), nullable=False), sa.Column("reason", sa.Text()), sa.Column("document_decisions", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index("ix_kyc_review_events_application_id", "kyc_review_events", ["application_id"])


def downgrade() -> None:
    op.drop_table("kyc_review_events"); op.drop_table("kyc_documents"); op.drop_table("kyc_applications")
    op.drop_index("ix_provider_profiles_user_id", table_name="provider_profiles"); op.drop_column("provider_profiles", "provider_type"); op.drop_column("provider_profiles", "user_id")
