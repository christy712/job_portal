from fastapi import APIRouter, Depends,HTTPException
from fastapi.responses import FileResponse
from app.db import get_db
import aiomysql,os
from app.utils.auth import get_current_user,require_role
from pydantic import BaseModel
router = APIRouter(prefix="/applications", tags=["Applications"])


class ApplyJob(BaseModel):
    job_id: int
    #  user_id: int
@router.post("/apply")
async def apply_to_job(data:ApplyJob,currentuser=Depends(get_current_user)):
    job_id=data.job_id
    user_id=currentuser['user_id']
    require_role(currentuser, ["applicant"])
    conn = await get_db()
    async with conn.cursor() as cur:
        await cur.execute(
            "select * from applications WHERE user_id=%s AND job_id=%s",
            (user_id,job_id)
        )
        apps = await cur.fetchone()
        if apps is not None:
            return {"message": "Already Applied"}
        else:
            await cur.execute(
                "INSERT INTO applications (job_id, user_id) VALUES (%s, %s)",
                (job_id, user_id)
            )
    conn.close()
    return {"message": "Applied successfully"}


@router.get("/user/list")
async def user_applications(currentuser=Depends(get_current_user)):
    user_id=currentuser['user_id']
    require_role(currentuser, ["applicant"])
    conn = await get_db()
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            SELECT a.id, j.title, j.company, j.location, a.applied_at,a.status
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
        # Verify job belongs to the current employer
        await cur.execute("SELECT user_id FROM jobs WHERE id=%s", (job_id,))
        job = await cur.fetchone()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if job[0] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Fetch applicants
        await cur.execute("""
            SELECT 
            a.id,
            u.id AS applicant_id,
            u.name AS applicant_name,
            u.email,
            u.skills,
            u.bio,
            a.status,
            a.applied_at
        FROM applications a
        JOIN users u ON a.user_id = u.id
        WHERE a.job_id = %s
        AND a.applied_at = (
            SELECT MAX(ap2.applied_at)
            FROM applications ap2
            WHERE ap2.user_id = a.user_id AND ap2.job_id = a.job_id
        )
        ORDER BY a.applied_at DESC;

               
        """, (job_id,))
        rows = await cur.fetchall()

    conn.close()

    # Convert rows (tuples) → list of dicts
    applicants = [
        {
            "id": r[0],
            "applicant_id": r[1],
            "applicant_name": r[2],
            "email": r[3],
            "skills": r[4],
            "bio": r[5],
            "status": r[6],
            "applied_on": r[7].isoformat() if r[7] else None,
        }
        for r in rows
    ]

    return applicants


@router.get("/resume/{applicant_id}")
async def download_resume(applicant_id: int):
    # require_role(current_user, ["employer"])

    conn = await get_db()
    async with conn.cursor() as cur:
        # Verify job belongs to employer
        # await cur.execute("SELECT user_id FROM jobs WHERE id=%s", (job_id,))
        # job = await cur.fetchone()
        # if not job or job[0] != current_user["user_id"]:
        #     raise HTTPException(status_code=403, detail="Not authorized")

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


