from fastapi import APIRouter, Depends, HTTPException,UploadFile,File
from fastapi.responses import JSONResponse
from app.db import get_db
import bcrypt,os,aiomysql
from app.utils.auth import get_current_user,require_role
from pydantic import BaseModel

UPLOAD_DIR = "uploads/resumes"
router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/register")
async def register_user(name: str, email: str, password: str, role: str = "applicant"):
    if role not in ("applicant", "employer"):
        raise HTTPException(status_code=400, detail="Invalid role")

    conn = await get_db()
    async with conn.cursor() as cur:
        await cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        if await cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        await cur.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, hashed, role)
        )
    conn.close()
    return {"message": f"User registered as {role} successfully"}


@router.get("/me")
async def get_profile(current_user=Depends(get_current_user)):
    conn = await get_db()
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("SELECT id, name, email, bio, skills, resume_url FROM users WHERE id=%s", 
                          (current_user["user_id"],))
        profile = await cur.fetchone()
    conn.close()
    return profile

@router.post("/upload_resume")
async def upload_resume(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    if current_user["role"] != "applicant":
        return JSONResponse(status_code=403, content={"detail": "Only applicants can upload resumes"})

    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, f"{current_user['user_id']}_{file.filename}")

    # Save file
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Update user table
    conn = await get_db()
    async with conn.cursor() as cur:
        await cur.execute("UPDATE users SET resume_url=%s WHERE id=%s", (file_path, current_user["user_id"]))
    conn.close()

    return {"message": "Resume uploaded successfully", "resume_url": file_path}




class ProfileUpdate(BaseModel):
    bio: str | None
    skills: str | None  # comma-separated

@router.put("/update_profile")
async def update_profile(profile: ProfileUpdate, current_user=Depends(get_current_user)):
    require_role(current_user, ["applicant"])

    conn = await get_db()
    async with conn.cursor() as cur:
        await cur.execute(
            "UPDATE users SET bio=%s, skills=%s WHERE id=%s",
            (profile.bio, profile.skills, current_user["user_id"])
        )
    conn.close()

    return {"message": "Profile updated successfully"}
