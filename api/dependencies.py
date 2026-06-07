from fastapi import HTTPException, Request, status

from storage.queries import get_user_by_session_token


SESSION_COOKIE = "hedwig_session"


def get_current_user(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user = get_user_by_session_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )
    return user
