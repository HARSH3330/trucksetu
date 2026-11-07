"""Optional private customer demand pins; no external API or backfill."""
from alembic import op
import sqlalchemy as sa
revision='20261025_29'
down_revision='20261023_28'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('transport_requests',sa.Column('pickup_location',sa.JSON(),nullable=True))
    op.add_column('transport_requests',sa.Column('destination_location',sa.JSON(),nullable=True))

def downgrade():
    raise RuntimeError('Private location history requires reviewed forward recovery')
