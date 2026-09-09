"""Link authenticated driver accounts to driver profiles.

Revision ID: 20260909_18
Revises: 20260906_17
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260909_18"
down_revision: str | None = "20260906_17"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("driver_profiles", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_driver_profiles_user_id_users",
        "driver_profiles",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_driver_profiles_user_id", "driver_profiles", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_driver_profiles_user_id", table_name="driver_profiles")
    op.drop_constraint("fk_driver_profiles_user_id_users", "driver_profiles", type_="foreignkey")
    op.drop_column("driver_profiles", "user_id")
