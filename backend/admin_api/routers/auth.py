from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt

from admin_api.schemas import LoginRequest, TokenResponse
from admin_api.settings import Settings, get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, settings: Settings = Depends(get_settings)) -> TokenResponse:
    if not settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ADMIN_PASSWORD is not configured",
        )
    if body.username != settings.admin_username or body.password != settings.admin_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    token = jwt.encode(
        {"sub": body.username, "exp": expire},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return TokenResponse(access_token=token)
