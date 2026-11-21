"""Remember the booking status when a dispute is raised so resolving it can restore the booking.

Additive and nullable. Existing disputes keep NULL; resolving one of those leaves the booking 'disputed'
and tells the administrator so. No data changes.
"""
from alembic import op
import sqlalchemy as sa
revision='20261120_33'
down_revision='20261120_32'
branch_labels=None
depends_on=None


def upgrade()->None:
    op.add_column('disputes',sa.Column('booking_status_before',sa.String(length=30),nullable=True))


def downgrade()->None:
    op.drop_column('disputes','booking_status_before')
