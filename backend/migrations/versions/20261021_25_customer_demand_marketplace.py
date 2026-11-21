"""Add customer-led demands and an independent connection-fee ledger.

Historical business rows remain legacy and are not reinterpreted.
"""
from alembic import op
import sqlalchemy as sa

revision = '20261021_25'
down_revision = '20261014_24'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('transport_requests', sa.Column('marketplace_mode', sa.String(30), nullable=False, server_default='legacy'))
    op.add_column('transport_requests', sa.Column('revision', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('cargo_items', sa.Column('packaging_type', sa.String(100), nullable=True))
    op.create_table('demand_drafts',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('customer_id', sa.Uuid(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table('demand_selections',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('request_id', sa.Uuid(), sa.ForeignKey('transport_requests.id'), nullable=False),
        sa.Column('quote_id', sa.Uuid(), sa.ForeignKey('quotes.id'), nullable=False),
        sa.Column('booking_id', sa.Uuid(), sa.ForeignKey('bookings.id'), nullable=False),
        sa.Column('customer_id', sa.Uuid(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('vehicle_id', sa.Uuid(), sa.ForeignKey('carrier_vehicles.id'), nullable=False),
        sa.Column('driver_id', sa.Uuid(), sa.ForeignKey('driver_profiles.id'), nullable=True),
        sa.Column('contact_kind', sa.String(20), nullable=False),
        sa.Column('contact_user_id', sa.Uuid(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('contact_phone_hash', sa.String(64), nullable=False),
        sa.Column('idempotency_key', sa.String(100), nullable=False),
        sa.Column('request_revision', sa.Integer(), nullable=False),
        sa.Column('quote_version', sa.Integer(), nullable=False),
        sa.Column('quote_snapshot', sa.JSON(), nullable=False),
        sa.Column('fee_snapshot', sa.JSON(), nullable=False),
        sa.Column('fee_amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('fee_tax', sa.Numeric(14, 2), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('status', sa.String(30), nullable=False, server_default='pending'),
        sa.Column('payment_status', sa.String(30), nullable=False, server_default='pending'),
        sa.Column('order_state', sa.String(30), nullable=False, server_default='not_created'),
        sa.Column('gateway_order_id', sa.String(100), nullable=True),
        sa.Column('gateway_payment_id', sa.String(100), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('fee_amount > 0 AND (fee_tax IS NULL OR fee_tax >= 0)', name='ck_connection_fee_positive'),
        sa.UniqueConstraint('booking_id'),
        sa.UniqueConstraint('idempotency_key'),
        sa.UniqueConstraint('gateway_order_id'),
        sa.UniqueConstraint('gateway_payment_id'),
    )
    op.create_table('connection_fee_events',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('selection_id', sa.Uuid(), sa.ForeignKey('demand_selections.id'), nullable=True),
        sa.Column('gateway_event_id', sa.String(200), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('outcome', sa.String(100), nullable=False),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('gateway_event_id'),
    )
    op.create_index('uq_demand_active_selection', 'demand_selections', ['request_id'], unique=True, postgresql_where=sa.text("status IN ('pending','paid')"))
    op.create_index('ix_demand_selection_vehicle', 'demand_selections', ['vehicle_id'])
    op.create_index('ix_demand_draft_customer', 'demand_drafts', ['customer_id'])
    op.create_index('ix_connection_event_selection', 'connection_fee_events', ['selection_id'])


def downgrade():
    raise RuntimeError('Connection-fee history requires a reviewed forward recovery, not destructive downgrade')
