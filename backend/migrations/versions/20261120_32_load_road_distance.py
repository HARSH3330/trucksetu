"""Store the road distance of each customer load (Google Routes, per load revision) so truck owners see km.

Additive and nullable; existing loads are filled in when truck owners next list them. No data changes.
"""
from alembic import op
import sqlalchemy as sa
revision='20261120_32'
down_revision='20261115_30'
branch_labels=None
depends_on=None


def upgrade()->None:
    op.add_column('transport_requests',sa.Column('route_distance_km',sa.Numeric(10,2),nullable=True))
    op.add_column('transport_requests',sa.Column('route_duration_minutes',sa.Integer(),nullable=True))
    op.add_column('transport_requests',sa.Column('route_revision',sa.Integer(),nullable=True))
    op.add_column('transport_requests',sa.Column('route_checked_at',sa.DateTime(timezone=True),nullable=True))


def downgrade()->None:
    for column in ['route_checked_at','route_revision','route_duration_minutes','route_distance_km']:
        op.drop_column('transport_requests',column)
