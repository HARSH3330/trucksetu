"""Let a superadmin verify one phone number on more than one account (the same person's customer and fleet accounts).

Self-service SMS verification still refuses a number verified elsewhere; that check lives in the API. No data changes.
"""
from alembic import op
import sqlalchemy as sa
revision='20261115_30'
down_revision='20261025_29'
branch_labels=None
depends_on=None


def upgrade()->None:
    op.drop_index('uq_users_verified_mobile',table_name='users')


def downgrade()->None:
    op.execute('LOCK TABLE users IN ACCESS EXCLUSIVE MODE')
    op.execute("""
    DO $$ BEGIN
        IF EXISTS (SELECT 1 FROM users WHERE mobile_verified GROUP BY mobile HAVING count(*)>1) THEN
            RAISE EXCEPTION 'Shared verified phone numbers exist; unverify the extra accounts before restoring the one-account rule';
        END IF;
    END $$;
    """)
    op.create_index('uq_users_verified_mobile','users',['mobile'],unique=True,postgresql_where=sa.text('mobile_verified'))
