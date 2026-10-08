"""Record versioned account Terms acceptance."""
import sqlalchemy as sa
from alembic import op

revision = "20261008_19"
down_revision = "20260909_18"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("terms_acceptances",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("version", sa.String(80), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("uq_terms_user_version", "terms_acceptances", ["user_id", "version"], unique=True)


def downgrade() -> None:
    op.drop_table("terms_acceptances")
