"""Add durable refund execution/reconciliation metadata; no automatic money movement."""
from alembic import op
import sqlalchemy as sa
revision='20261023_28'
down_revision='20261023_27'
branch_labels=None
depends_on=None


def upgrade():
    for name in ('gateway_payment_id','gateway_refund_id','idempotency_key'):
        op.add_column('connection_fee_refund_requests',sa.Column(name,sa.String(100)))
    op.create_unique_constraint('uq_connection_refund_gateway_id','connection_fee_refund_requests',['gateway_refund_id'])
    op.create_unique_constraint('uq_connection_refund_idempotency','connection_fee_refund_requests',['idempotency_key'])
    op.add_column('connection_fee_refund_requests',sa.Column('request_payload',sa.JSON()))
    op.add_column('connection_fee_refund_requests',sa.Column('attempt_count',sa.Integer(),nullable=False,server_default='0'))
    op.add_column('connection_fee_refund_requests',sa.Column('last_attempt_at',sa.DateTime(timezone=True)))
    op.add_column('connection_fee_refund_requests',sa.Column('last_error_code',sa.String(60)))
    op.add_column('connection_fee_refund_requests',sa.Column('reconciled_at',sa.DateTime(timezone=True)))


def downgrade():
    raise RuntimeError('Refund execution history requires reviewed forward recovery')
