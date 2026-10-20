"""Browser-only HttpOnly cookie transport; existing auth remains authoritative."""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import auth
from app.core.config import settings
from app.core.database import get_db

COOKIE='transivox_refresh'
PATH='/api/v1/auth/session'


def require_browser_origin(request:Request):
    # Explicit origin + non-simple custom header requires a successful CORS
    # preflight for cross-origin browser requests. No wildcard/reflected origin.
    if request.headers.get('origin') not in settings.ALLOWED_ORIGINS or request.headers.get('x-transivox-csrf')!='1':
        raise HTTPException(403,'Untrusted browser session request')


def require_refresh_cookie(request:Request):
    value=request.cookies.get(COOKIE)
    if not value:raise HTTPException(401,'Sign in to restore your session')
    return value


def options():
    local=settings.APP_ENV in {'test','development'}
    return {'path':PATH,'httponly':True,'secure':not local,'samesite':'lax' if local else settings.AUTH_COOKIE_SAMESITE}


def cookie_result(result:dict,response:Response):
    result=dict(result)
    token=result.pop('refresh_token')
    response.set_cookie(COOKIE,token,max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS*86400,**options())
    response.headers['Cache-Control']='no-store'
    return result


router=APIRouter(prefix=PATH,tags=['browser sessions'],dependencies=[Depends(require_browser_origin)])


@router.post('/login')
async def login(payload:auth.LoginInput,request:Request,response:Response,db:AsyncSession=Depends(get_db)):
    result=await auth.login(payload,request,db)
    # Commit credential/session creation before advertising a usable cookie.
    await db.commit()
    return cookie_result(result,response)


@router.post('/signup',status_code=201)
async def signup(payload:auth.SignupInput,request:Request,response:Response,db:AsyncSession=Depends(get_db)):
    result=await auth.signup(payload,request,db)
    await db.commit()
    return cookie_result(result,response)


@router.post('/refresh')
async def refresh(request:Request,response:Response,token:str=Depends(require_refresh_cookie),db:AsyncSession=Depends(get_db)):
    result=await auth.refresh(auth.RefreshInput(refresh_token=token),request,db)
    await db.commit()
    return cookie_result(result,response)


@router.post('/migrate')
async def migrate(payload:auth.RefreshInput,request:Request,response:Response,db:AsyncSession=Depends(get_db)):
    result=await auth.refresh(payload,request,db)
    await db.commit()
    return cookie_result(result,response)


@router.post('/logout',status_code=204)
async def logout(request:Request,response:Response,db:AsyncSession=Depends(get_db)):
    token=request.cookies.get(COOKIE)
    if token:await auth.logout(auth.RefreshInput(refresh_token=token),db)
    response.delete_cookie(COOKIE,**options())
    response.headers['Cache-Control']='no-store'
