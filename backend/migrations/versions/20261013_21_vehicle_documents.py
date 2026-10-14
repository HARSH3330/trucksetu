"""Private vehicle documents with auditable reviewer decisions."""
from alembic import op
import sqlalchemy as sa

revision='20261013_21'
down_revision='20261013_20'
branch_labels=None
depends_on=None

def upgrade()->None:
    op.create_table('vehicle_documents',
        sa.Column('id',sa.Uuid(),primary_key=True),
        sa.Column('vehicle_id',sa.Uuid(),sa.ForeignKey('carrier_vehicles.id'),nullable=False),
        sa.Column('document_type',sa.String(30),nullable=False),
        sa.Column('storage_key',sa.String(500),nullable=False,unique=True),
        sa.Column('storage_version_id',sa.String(255),nullable=False),
        sa.Column('original_filename',sa.String(255),nullable=False),
        sa.Column('content_type',sa.String(100),nullable=False),
        sa.Column('size_bytes',sa.Integer(),nullable=False),
        sa.Column('expires_on',sa.Date(),nullable=False),
        sa.Column('status',sa.String(30),nullable=False),
        sa.Column('reviewed_by',sa.Uuid(),sa.ForeignKey('users.id')),
        sa.Column('reviewed_at',sa.DateTime(timezone=True)),
        sa.Column('review_reason',sa.Text()),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_index('ix_vehicle_document_vehicle_type','vehicle_documents',['vehicle_id','document_type'])

def downgrade()->None:
    op.drop_table('vehicle_documents')
