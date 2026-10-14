"""Reserve canonical phone numbers only after ownership verification.

Refuse ambiguous verified claims; never pick an owner or delete a record.
"""
from alembic import op
import sqlalchemy as sa

revision='20261014_22'
down_revision='20261013_21'
branch_labels=None
depends_on=None

# Same normalization contract as canonical_mobile: local ten-digit Indian
# contacts receive 91; already country-coded contacts receive only a leading +.
CANONICAL="CASE WHEN mobile !~ '^\\+' AND length(mobile)=10 THEN '+91'||mobile ELSE '+'||ltrim(mobile,'+') END"
VALID=r"^\+?[1-9][0-9]{7,14}$"


def upgrade()->None:
    op.execute('LOCK TABLE users IN ACCESS EXCLUSIVE MODE')
    op.execute(f"""
    DO $$ BEGIN
        IF EXISTS (SELECT 1 FROM users WHERE mobile_verified AND (mobile IS NULL OR mobile !~ '{VALID}')) THEN
            RAISE EXCEPTION 'Verified phone migration blocked: invalid verified phone requires explicit remediation';
        END IF;
        IF EXISTS (SELECT 1 FROM users WHERE mobile_verified GROUP BY {CANONICAL} HAVING count(*)>1) THEN
            RAISE EXCEPTION 'Verified phone migration blocked: conflicting verified claims require explicit remediation';
        END IF;
    END $$;
    """)
    # This constraint comes from the real Phase 11 Alembic migration, not
    # create_all metadata. The ordinary lookup index remains in place.
    op.drop_constraint('users_mobile_key','users',type_='unique')
    op.execute(f"UPDATE users SET mobile={CANONICAL} WHERE mobile IS NOT NULL AND mobile ~ '{VALID}'")
    op.create_check_constraint('ck_users_verified_mobile_canonical','users',r"NOT mobile_verified OR (mobile IS NOT NULL AND mobile ~ '^\+[1-9][0-9]{7,14}$')")
    op.create_index('uq_users_verified_mobile','users',['mobile'],unique=True,postgresql_where=sa.text('mobile_verified'))


def downgrade()->None:
    op.execute('LOCK TABLE users IN ACCESS EXCLUSIVE MODE')
    op.execute("""
    DO $$ BEGIN
        IF EXISTS (SELECT 1 FROM users WHERE mobile IS NOT NULL GROUP BY mobile HAVING count(*)>1) THEN
            RAISE EXCEPTION 'Phone ownership downgrade blocked: duplicate claims need an explicit recovery plan';
        END IF;
    END $$;
    """)
    op.drop_index('uq_users_verified_mobile',table_name='users')
    op.drop_constraint('ck_users_verified_mobile_canonical','users',type_='check')
    op.create_unique_constraint('users_mobile_key','users',['mobile'])
