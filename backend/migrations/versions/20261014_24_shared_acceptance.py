"""Route-bound provider quotes with explicit idempotent customer acceptance."""
from alembic import op
import sqlalchemy as sa

revision = '20261014_24'
down_revision = '20261014_23'
branch_labels = None
depends_on = None


def upgrade():
    for table in ['transport_requests','quotes']:
        op.add_column(table, sa.Column('available_route_id',sa.Uuid(),nullable=True))
        op.create_foreign_key(f'fk_{table}_shared_route',table,'available_routes',['available_route_id'],['id'])
    op.add_column('quotes',sa.Column('expires_at',sa.DateTime(timezone=True),nullable=True))
    op.add_column('quotes',sa.Column('price_breakdown',sa.JSON(),nullable=True))
    op.add_column('quote_versions',sa.Column('snapshot',sa.JSON(),nullable=True))
    op.add_column('bookings',sa.Column('acceptance_key',sa.String(100),nullable=True))
    op.create_unique_constraint('uq_booking_acceptance_key','bookings',['acceptance_key'])


def downgrade():
    raise RuntimeError('Shared acceptance snapshots require a reviewed forward fix, not destructive downgrade')
