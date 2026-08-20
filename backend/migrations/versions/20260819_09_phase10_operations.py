"""Phase 10 audit and analytics.

Revision ID: 20260819_09
Revises: 20260819_08
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
revision: str="20260819_09";down_revision: str|None="20260819_08";branch_labels: Sequence[str]|None=None;depends_on: Sequence[str]|None=None


def upgrade()->None:
    op.create_table("audit_logs",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("actor_id",sa.Uuid()),sa.Column("action",sa.String(100),nullable=False),sa.Column("entity_type",sa.String(50),nullable=False),sa.Column("entity_id",sa.Uuid()),sa.Column("before",sa.JSON()),sa.Column("after",sa.JSON()),sa.Column("request_id",sa.String(100)),sa.Column("ip_address",sa.String(64)),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_index("ix_audit_logs_actor_id","audit_logs",["actor_id"]);op.create_index("ix_audit_logs_request_id","audit_logs",["request_id"]);op.create_index("ix_audit_entity_created","audit_logs",["entity_type","entity_id","created_at"])
    op.create_table("analytics_events",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("event_name",sa.String(100),nullable=False),sa.Column("user_id",sa.Uuid()),sa.Column("anonymous_id",sa.String(100)),sa.Column("entity_type",sa.String(50)),sa.Column("entity_id",sa.Uuid()),sa.Column("properties",sa.JSON(),nullable=False),sa.Column("occurred_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_analytics_events_user_id","analytics_events",["user_id"]);op.create_index("ix_analytics_events_anonymous_id","analytics_events",["anonymous_id"]);op.create_index("ix_analytics_event_created","analytics_events",["event_name","occurred_at"])


def downgrade()->None:
    op.drop_table("analytics_events");op.drop_table("audit_logs")
