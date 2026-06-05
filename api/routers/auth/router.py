from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError

from api.dependencies import SESSION_COOKIE
from api.routers.auth.schemas import LoginPayload, SignupPayload
from storage.queries import (
    create_session,
    create_user,
    delete_session,
    get_user_by_email,
    get_user_by_session_token,
    public_user,
)
from storage.security import (
    SESSION_SECONDS,
    hash_password,
    new_session_token,
    session_expiry,
    verify_password,
)


router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_session_cookie(response: Response, user_id: int):
    token = new_session_token()
    expires_at = session_expiry()
    create_session(user_id, token, expires_at)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=SESSION_SECONDS,
    )


@router.post("/signup")
async def signup(payload: SignupPayload, response: Response):
    if "@" not in payload.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter a valid email address.",
        )

    if len(payload.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters.",
        )

    try:
        user = create_user(
            email=payload.email,
            password_hash=hash_password(payload.password),
            display_name=payload.display_name,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    _set_session_cookie(response, user["id"])
    return {"user": public_user(user)}


@router.post("/login")
async def login(payload: LoginPayload, response: Response):
    user = get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    _set_session_cookie(response, user["id"])
    return {"user": public_user(user)}


@router.post("/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        delete_session(token)
    response.delete_cookie(SESSION_COOKIE)
    return {"success": True}


@router.get("/me")
async def me(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    user = get_user_by_session_token(token) if token else None
    return {"user": public_user(user) if user else None}
