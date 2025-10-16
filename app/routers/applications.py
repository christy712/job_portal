from fastapi import APIRouter, Depends,HTTPException,FileResponse
from app.db import get_db
import aiomysql,os
from app.utils.auth import get_current_user,require_role
from pydantic import BaseModel
router = APIRouter(prefix="/applications", tags=["Applications"])

@router.post("/apply")
async def apply_to_job(job_id: int, user_id: int):
    require_role(Depends(get_current_user), ["applicant"])
    conn = await get_db()
    async with conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO applications (job_id, user_id) VALUES (%s, %s)",
            (job_id, user_id)
        )
    conn.close()
    return {"message": "Applied successfully"}


@router.get("/user/{user_id}")
async def user_applications(user_id: int):
    require_role(Depends(get_current_user), ["applicant"])
    conn = await get_db()
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            SELECT a.id, j.title, j.company, j.location, a.applied_at
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.user_id=%s
            """,
            (user_id,)
        )
        apps = await cur.fetchall()
    conn.close()
    return apps


@router.get("/job/{job_id}/applicants")
async def get_applicants(job_id: int, current_user=Depends(get_current_user)):
    require_role(current_user, ["employer"])

    conn = await get_db()
    async with conn.cursor() as cur:
        # Verify job belongs to current employer
        await cur.execute("SELECT user_id FROM jobs WHERE id=%s", (job_id,))
        job = await cur.fetchone()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if job[0] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Get applicants
        await cur.execute("""
            SELECT a.id, u.id AS applicant_id, u.name, u.email, u.skills, u.bio, u.resume_url, a.status, a.applied_at
            FROM applications a
            JOIN users u ON a.user_id = u.id
            WHERE a.job_id=%s
            ORDER BY a.applied_at DESC
        """, (job_id,))
        applicants = await cur.fetchall()
    conn.close()
    return applicants


@router.get("/resume/{applicant_id}")
async def download_resume(applicant_id: int, job_id: int, current_user=Depends(get_current_user)):
    require_role(current_user, ["employer"])

    conn = await get_db()
    async with conn.cursor() as cur:
        # Verify job belongs to employer
        await cur.execute("SELECT user_id FROM jobs WHERE id=%s", (job_id,))
        job = await cur.fetchone()
        if not job or job[0] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Get applicant resume
        await cur.execute("SELECT resume_url FROM users WHERE id=%s", (applicant_id,))
        resume = await cur.fetchone()
        if not resume or not resume[0]:
            raise HTTPException(status_code=404, detail="Resume not found")
        resume_path = resume[0]

    conn.close()
    if not os.path.isfile(resume_path):
        raise HTTPException(status_code=404, detail="Resume file missing")
    return FileResponse(resume_path, filename=os.path.basename(resume_path))



class StatusUpdate(BaseModel):
    status: str  # 'reviewed', 'shortlisted', 'rejected'

@router.put("/update_status/{application_id}")
async def update_status(application_id: int, payload: StatusUpdate, current_user=Depends(get_current_user)):
    require_role(current_user, ["employer"])
    if payload.status not in ("reviewed", "shortlisted", "rejected"):
        raise HTTPException(status_code=400, detail="Invalid status")

    conn = await get_db()
    async with conn.cursor() as cur:
        # Verify application belongs to employer's job
        await cur.execute("""
            SELECT j.user_id 
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.id=%s
        """, (application_id,))
        owner = await cur.fetchone()
        if not owner or owner[0] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        await cur.execute("UPDATE applications SET status=%s WHERE id=%s", (payload.status, application_id))
    conn.close()
    return {"message": f"Application status updated to {payload.status}"}


