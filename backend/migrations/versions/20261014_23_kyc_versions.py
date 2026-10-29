"""Pin provider KYC evidence to immutable storage versions.

Legacy NULL references are intentionally not inferred from current objects.
Owner approved re-verification before new operations on 2026-10-14.
"""
from alembic import op
import sqlalchemy as sa

revision = '20261014_23'
down_revision = '20261014_22'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('kyc_documents', sa.Column('storage_version_id', sa.String(255), nullable=True))
    # Every pre-migration file is unbound. Preserve files and prior review
    # events; make the new operational gate explicit rather than infer bytes.
    op.execute("""
        INSERT INTO audit_logs (id, action, entity_type, entity_id, before, after)
        SELECT gen_random_uuid(), 'kyc.version_reverification_required', 'provider', id,
               json_build_object('kyc_status', kyc_status),
               json_build_object('kyc_status', 'resubmit_required', 'migration', '20261014_23')
        FROM provider_profiles WHERE kyc_status = 'verified'
    """)
    op.execute("UPDATE provider_profiles SET kyc_status = 'resubmit_required' WHERE kyc_status = 'verified'")
    op.execute("""
        UPDATE kyc_applications
        SET status = 'resubmit_required',
            decision_reason = concat_ws(E'\\n', decision_reason,
                'Immutable version protection rollout: replace legacy documents and request re-verification.')
        WHERE status = 'verified'
    """)
    # History records the old decisions; rejected rows allow the existing
    # replacement workflow to register genuinely new scanned object versions.
    op.execute("""
        UPDATE kyc_documents SET status = 'rejected',
            rejection_reason = concat_ws(E'\\n', rejection_reason,
                'Legacy unbound document: replace with a version-pinned upload.')
        WHERE status != 'rejected' AND storage_version_id IS NULL
    """)


def downgrade() -> None:
    # Dropping pins would permit approved bytes to change after rollback.
    raise RuntimeError('KYC version protection cannot be safely downgraded; use a reviewed forward fix')
