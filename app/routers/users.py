from fastapi import APIRouter, Depends, HTTPException,UploadFile,File,Form
from fastapi.responses import JSONResponse
from app.db import get_db
import bcrypt,os,aiomysql
from app.utils.auth import get_current_user,require_role
from pydantic import BaseModel

UPLOAD_DIR = "uploads/resumes"
router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/register")
async def register_user(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    bio: str | None = Form(None),
    resume: UploadFile | None = File(None),
):
    if role not in ("applicant", "employer"):
        raise HTTPException(status_code=400, detail="Invalid role")

    conn = await get_db()
    async with conn.cursor() as cur:
        # Check if email already exists
        await cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        if await cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

        # Hash password
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Insert user
        await cur.execute(
            "INSERT INTO users (name, email, password, role, bio) VALUES (%s, %s, %s, %s, %s)",
            (name, email, hashed, role, bio)
        )
        await conn.commit()

        # Save resume if applicant
        resume_path = None
        if role == "applicant" and resume:
            resume_path = os.path.join(UPLOAD_DIR, resume.filename)
            with open(resume_path, "wb") as f:
                f.write(await resume.read())
            await cur.execute(
                "UPDATE users SET resume_url=%s WHERE email=%s",
                (resume_path, email)
            )
            await conn.commit()

    conn.close()
    return JSONResponse(content={"message": f"User registered as {role} successfully"})


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




# class ProfileUpdate(BaseModel):
#     bio: str | None
#     skills: str | None  # comma-separated

@router.put("/update_profile")
async def update_profile(
    name: str = Form(...),
    bio: str | None = Form(None),
    resume: UploadFile | None = File(None),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]
    role = current_user["role"]

    conn = await get_db()
    async with conn.cursor() as cur:
        # Update name and bio
        await cur.execute(
            "UPDATE users SET name=%s, bio=%s WHERE id=%s",
            (name, bio if role == "applicant" else None, user_id)
        )

        # Update resume for applicant
        if role == "applicant" and resume:
            resume_path = os.path.join(UPLOAD_DIR, resume.filename)
            with open(resume_path, "wb") as f:
                f.write(await resume.read())
            await cur.execute(
                "UPDATE users SET resume_path=%s WHERE id=%s",
                (resume_path, user_id)
            )

        await conn.commit()

        # Fetch updated info
        await cur.execute("SELECT id, name, email, role, bio, resume_path FROM users WHERE id=%s", (user_id,))
        updated_user = await cur.fetchone()

    conn.close()

    return {
        "id": updated_user[0],
        "name": updated_user[1],
        "email": updated_user[2],
        "role": updated_user[3],
        "bio": updated_user[4],
        "resume_path": updated_user[5],
        "message": "Profile updated successfully"
    }
