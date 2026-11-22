"""Record explicit contact reveal, full pre-reveal refund obligations and single-use credits."""
from alembic import op
import sqlalchemy as sa
revision='20261023_27'
down_revision='20261023_26'
branch_labels=None
depends_on=None


def upgrade():
    op.add_column('demand_selections',sa.Column('contact_revealed_at',sa.DateTime(timezone=True)))
    op.add_column('demand_selections',sa.Column('cancelled_at',sa.DateTime(timezone=True)))
    # Historical contact reads already committed their audit before returning a number.
    op.execute("UPDATE demand_selections s SET contact_revealed_at=e.first_access FROM (SELECT entity_id,MIN(created_at) first_access FROM audit_logs WHERE action='connection.contact_accessed' GROUP BY entity_id) e WHERE e.entity_id=s.id")
    op.create_table('connection_fee_refund_requests',
        sa.Column('id',sa.Uuid(),primary_key=True),
        sa.Column('selection_id',sa.Uuid(),sa.ForeignKey('demand_selections.id'),nullable=False,unique=True),
        sa.Column('amount',sa.Numeric(14,2),nullable=False),
        sa.Column('tax_amount',sa.Numeric(14,2)),sa.Column('currency',sa.String(3),nullable=False),
        sa.Column('status',sa.String(30),nullable=False),sa.Column('reason',sa.Text(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_table('connection_fee_credits',
        sa.Column('id',sa.Uuid(),primary_key=True),
        sa.Column('customer_id',sa.Uuid(),sa.ForeignKey('users.id'),nullable=False),
        sa.Column('source_selection_id',sa.Uuid(),sa.ForeignKey('demand_selections.id'),nullable=False,unique=True),
        sa.Column('issued_by',sa.Uuid(),sa.ForeignKey('users.id'),nullable=False),
        sa.Column('reason',sa.Text(),nullable=False),sa.Column('status',sa.String(30),nullable=False),
        sa.Column('reserved_selection_id',sa.Uuid(),sa.ForeignKey('demand_selections.id'),unique=True),
        sa.Column('redeemed_selection_id',sa.Uuid(),sa.ForeignKey('demand_selections.id'),unique=True),
        sa.Column('redeemed_at',sa.DateTime(timezone=True)),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.add_column('demand_selections',sa.Column('credit_id',sa.Uuid(),sa.ForeignKey('connection_fee_credits.id')))


def downgrade():
    raise RuntimeError('Contact access and financial history require reviewed forward recovery')
