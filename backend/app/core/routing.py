"""Reject invalid bearer credentials before resolving database dependencies.

The existing current_user/require_roles dependencies remain authoritative for
account status, ownership and roles. Public routes have no bearer preflight.
"""
import uuid

from fastapi import HTTPException, Request
from fastapi.routing import APIRoute
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.core.security import verify_token


def _bearer_dependency(dependant):
    if isinstance(dependant.call, OAuth2PasswordBearer):
        return dependant.call
    for child in dependant.dependencies:
        bearer = _bearer_dependency(child)
        if bearer is not None:
            return bearer
    return None


class AuthenticationFirstRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()
        bearer = _bearer_dependency(self.dependant)
        if bearer is None:
            return original

        async def authenticated(request: Request):
            token = await bearer(request)
            try:
                claims = verify_token(token, 'access')
                uuid.UUID(claims['sub'])
            except (JWTError, KeyError, ValueError, TypeError) as exc:
                raise HTTPException(401, 'Invalid access token', headers={'WWW-Authenticate': 'Bearer'}) from exc
            return await original(request)
        return authenticated
