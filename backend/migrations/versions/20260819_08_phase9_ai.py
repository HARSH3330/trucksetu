"""Phase 9 AI analyses and human-reviewed risk flags.

Revision ID: 20260819_08
Revises: 20260819_07
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
revision: str="20260819_08";down_revision: str|None="20260819_07";branch_labels: Sequence[str]|None=None;depends_on: Sequence[str]|None=None


def upgrade() -> None:
    op.create_table("ai_analyses",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("analysis_type",sa.String(50),nullable=False),sa.Column("entity_type",sa.String(50)),sa.Column("entity_id",sa.Uuid()),sa.Column("provider",sa.String(30),nullable=False),sa.Column("input_snapshot",sa.JSON(),nullable=False),sa.Column("output",sa.JSON(),nullable=False),sa.Column("fallback_used",sa.Boolean(),nullable=False,server_default=sa.false()),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_index("ix_ai_analyses_analysis_type","ai_analyses",["analysis_type"]);op.create_index("ix_ai_analyses_entity_id","ai_analyses",["entity_id"])
    op.create_table("ai_risk_flags",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("quote_id",sa.Uuid(),sa.ForeignKey("quotes.id"),nullable=False),sa.Column("flag_code",sa.String(100),nullable=False),sa.Column("severity",sa.String(20),nullable=False,server_default="review"),sa.Column("explanation",sa.Text(),nullable=False),sa.Column("status",sa.String(20),nullable=False,server_default="open"),sa.Column("reviewed_by",sa.Uuid()),sa.Column("reviewed_at",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_index("ix_ai_risk_flags_quote_id","ai_risk_flags",["quote_id"])


def downgrade() -> None:
    op.drop_table("ai_risk_flags");op.drop_table("ai_analyses")
