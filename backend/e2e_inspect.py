"""Read-only, narrowly scoped persisted-state assertions for local KYC tests."""
import json
import sys
import uuid

import psycopg
from psycopg.rows import dict_row

from e2e_database import safe_database_url


def snapshot(application_id: str) -> dict:
    identifier = uuid.UUID(application_id)
    url = safe_database_url().replace('postgresql+psycopg://', 'postgresql://', 1)
    with psycopg.connect(url, row_factory=dict_row) as connection:
        connection.execute('SET TRANSACTION READ ONLY')
        application = connection.execute('SELECT a.status, a.decision_reason, p.kyc_status, p.active FROM kyc_applications a JOIN provider_profiles p ON p.id=a.provider_id WHERE a.id=%s', (identifier,)).fetchone()
        documents = connection.execute('SELECT id::text, document_type, status, rejection_reason FROM kyc_documents WHERE application_id=%s ORDER BY id', (identifier,)).fetchall()
        reviews = connection.execute('SELECT previous_status, new_status, reason, document_decisions FROM kyc_review_events WHERE application_id=%s ORDER BY created_at, id', (identifier,)).fetchall()
        return {'application':application, 'documents':documents, 'reviews':reviews}


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'owner-required':
        from app.api.kyc import REQUIRED
        print(json.dumps(sorted(REQUIRED['owner'])))
    elif len(sys.argv) == 2:
        try:
            print(json.dumps(snapshot(sys.argv[1])))
        except Exception:
            raise SystemExit('Local KYC state inspection failed; connection details redacted')
    else:
        raise SystemExit('Usage: python -m e2e_inspect <application UUID>|owner-required')
