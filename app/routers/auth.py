from fastapi import APIRouter, HTTPException
from app.db import get_db
from app.utils.auth import create_access_token
import bcrypt

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login(email: str, password: str):
    conn = await get_db()
    async with conn.cursor() as cur:
        await cur.execute("SELECT id, name, password, role FROM users WHERE email=%s", (email.strip(),))
        user = await cur.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id, name, hashed_pw, role = user
    if not bcrypt.checkpw(password.strip().encode(), hashed_pw.encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "user_id": user_id,
        "name": name,
        "email": email,
        "role": role
    })
    return {"access_token": token, "role": role, "token_type": "bearer"}

