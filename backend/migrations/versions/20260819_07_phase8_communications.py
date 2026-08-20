"""Phase 8 notifications and booking chat.

Revision ID: 20260819_07
Revises: 20260819_06
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
revision: str="20260819_07";down_revision: str|None="20260819_06";branch_labels: Sequence[str]|None=None;depends_on: Sequence[str]|None=None


def upgrade() -> None:
    op.create_table("notification_preferences",sa.Column("user_id",sa.Uuid(),primary_key=True),sa.Column("in_app",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("email",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("sms",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("whatsapp",sa.Boolean(),nullable=False,server_default=sa.false()),sa.Column("quiet_hours_start",sa.String(5)),sa.Column("quiet_hours_end",sa.String(5)),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_table("notifications",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("user_id",sa.Uuid(),nullable=False),sa.Column("event_type",sa.String(100),nullable=False),sa.Column("title",sa.String(200),nullable=False),sa.Column("body",sa.Text(),nullable=False),sa.Column("entity_type",sa.String(50)),sa.Column("entity_id",sa.Uuid()),sa.Column("data",sa.JSON(),nullable=False),sa.Column("read_at",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_index("ix_notifications_user_unread","notifications",["user_id","read_at","created_at"])
    op.create_table("notification_deliveries",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("notification_id",sa.Uuid(),sa.ForeignKey("notifications.id",ondelete="CASCADE"),nullable=False),sa.Column("channel",sa.String(20),nullable=False),sa.Column("recipient",sa.String(250),nullable=False),sa.Column("status",sa.String(30),nullable=False,server_default="queued"),sa.Column("provider_reference",sa.String(200)),sa.Column("attempts",sa.Integer(),nullable=False,server_default="0"),sa.Column("last_error",sa.Text()),sa.Column("next_attempt_at",sa.DateTime(timezone=True)),sa.Column("sent_at",sa.DateTime(timezone=True)),sa.CheckConstraint("channel IN ('in_app','email','sms','whatsapp')",name="ck_notification_channel"))
    op.create_index("ix_notification_delivery_queue","notification_deliveries",["status","next_attempt_at"])
    op.create_table("conversations",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("booking_id",sa.Uuid(),sa.ForeignKey("bookings.id"),nullable=False,unique=True),sa.Column("status",sa.String(20),nullable=False,server_default="active"),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_table("conversation_participants",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("conversation_id",sa.Uuid(),sa.ForeignKey("conversations.id",ondelete="CASCADE"),nullable=False),sa.Column("user_id",sa.Uuid(),nullable=False),sa.Column("role",sa.String(20),nullable=False),sa.Column("last_read_at",sa.DateTime(timezone=True)),sa.UniqueConstraint("conversation_id","user_id",name="uq_conversation_participant"))
    op.create_index("ix_conversation_participants_user_id","conversation_participants",["user_id"])
    op.create_table("messages",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("conversation_id",sa.Uuid(),sa.ForeignKey("conversations.id",ondelete="CASCADE"),nullable=False),sa.Column("sender_id",sa.Uuid(),nullable=False),sa.Column("body",sa.Text(),nullable=False),sa.Column("attachment_keys",sa.JSON(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.Column("deleted_at",sa.DateTime(timezone=True)))
    op.create_index("ix_messages_conversation_created","messages",["conversation_id","created_at"])


def downgrade() -> None:
    op.drop_table("messages");op.drop_table("conversation_participants");op.drop_table("conversations");op.drop_table("notification_deliveries");op.drop_table("notifications");op.drop_table("notification_preferences")
