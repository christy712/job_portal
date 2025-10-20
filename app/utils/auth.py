import jwt
import datetime
from fastapi import HTTPException, Request
from app.config import settings

JWT_SECRET = settings.JWT_SECRET
JWT_ALGORITHM = settings.JWT_ALGORITHM
TOKEN_BLACKLIST = set()


def create_access_token(data: dict, expires_delta: int = 3600):
    payload = data.copy()
    payload["exp"] = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_delta)
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token: str):
    if token in TOKEN_BLACKLIST:
        raise HTTPException(status_code=401, detail="Token has been revoked")
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(request: Request):
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")

    token = token.replace("Bearer ", "")
    decoded = verify_token(token)
    return decoded


def require_role(current_user, allowed_roles: list[str]):
    if current_user["role"] not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}"
        )
    

def destroy_token(token: str):
    """
    Add a token to blacklist so it cannot be used anymore.
    """
    TOKEN_BLACKLIST.add(token)
