"""Local-only session expiry/revocation fixtures, never registered as API routes."""
import sys
import uuid

import psycopg

from e2e_database import safe_database_url


def change_session(action: str, user_id: str) -> None:
    raw = safe_database_url().replace('postgresql+psycopg://', 'postgresql://', 1)
    identifier = uuid.UUID(user_id)
    if action not in {'expire', 'revoke'}:
        raise ValueError('Unknown local session action')
    column = 'expires_at' if action == 'expire' else 'revoked_at'
    with psycopg.connect(raw) as connection:
        connection.execute(
            f'UPDATE refresh_sessions SET {column}=now()-interval \'1 second\' '
            'WHERE user_id=%s AND revoked_at IS NULL', (identifier,),
        )


if __name__ == '__main__':
    try:
        change_session(*sys.argv[1:])
    except Exception:
        raise SystemExit('Local session fixture failed (connection details redacted)') from None
