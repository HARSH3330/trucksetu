"""Add private customer review without reinterpreting provider/vehicle evidence."""
from alembic import op
import sqlalchemy as sa
revision='20261023_26'
down_revision='20261021_25'
branch_labels=None
depends_on=None


def upgrade():
    op.create_table('customer_kyc_applications',
        sa.Column('id',sa.Uuid(),primary_key=True),
        sa.Column('user_id',sa.Uuid(),sa.ForeignKey('users.id'),nullable=False),
        sa.Column('status',sa.String(30),nullable=False),
        sa.Column('policy_version',sa.String(80),nullable=False),
        sa.Column('required_documents',sa.JSON(),nullable=False),
        sa.Column('consent_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
        sa.Column('decision_reason',sa.Text()),
        sa.Column('reviewed_by',sa.Uuid(),sa.ForeignKey('users.id')),
        sa.Column('reviewed_at',sa.DateTime(timezone=True)))
    op.create_index('ix_customer_kyc_applications_user_id','customer_kyc_applications',['user_id'])
    op.create_index('uq_customer_kyc_active','customer_kyc_applications',['user_id'],unique=True,postgresql_where=sa.text("status IN ('registered','under_review','resubmit_required','verified')"))
    op.create_table('customer_kyc_documents',
        sa.Column('id',sa.Uuid(),primary_key=True),
        sa.Column('application_id',sa.Uuid(),sa.ForeignKey('customer_kyc_applications.id'),nullable=False),
        sa.Column('document_type',sa.String(50),nullable=False),
        sa.Column('storage_key',sa.String(500),nullable=False),
        sa.Column('storage_version_id',sa.String(255),nullable=False),
        sa.Column('content_type',sa.String(100),nullable=False),
        sa.Column('size_bytes',sa.Integer(),nullable=False),
        sa.Column('status',sa.String(30),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()))
    op.create_index('ix_customer_kyc_documents_application_id','customer_kyc_documents',['application_id'])
    op.create_index('uq_customer_kyc_current_document','customer_kyc_documents',['application_id','document_type'],unique=True,postgresql_where=sa.text("status != 'rejected'"))


def downgrade():
    raise RuntimeError('Customer identity history requires reviewed forward recovery')
