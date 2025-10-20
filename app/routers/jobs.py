from fastapi import APIRouter, Depends,HTTPException,Query
import aiomysql
from app.db import get_db
from app.utils.auth import get_current_user,require_role
from pydantic import BaseModel

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("/")
async def list_jobs():
    conn = await get_db()
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("SELECT * FROM jobs ORDER BY created_at DESC")
        jobs = await cur.fetchall()
    conn.close()
    return jobs


class CreateJob(BaseModel):
    title: str
    description: str
    company: str
    location: str

@router.post("/")
async def create_job(data:CreateJob,current_user=Depends(get_current_user)):
    
    title=data.title
    description=data.description
    company=data.company
    location=data.location
    require_role(current_user, ["employer"])
    conn = await get_db()
    async with conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO jobs (title, description, company, location, user_id) VALUES (%s, %s, %s, %s, %s)",
            (title, description, company, location, current_user["user_id"])
        )
    conn.close()
    return {"message": "Job created successfully"}




# Job Deletion /Close Routes


@router.delete("/delete/{job_id}")
async def delete_job(job_id: int, current_user=Depends(get_current_user)):
    require_role(current_user, ["employer"])
    conn = await get_db()
    async with conn.cursor() as cur:
        # Check if job belongs to user
        await cur.execute("SELECT user_id FROM jobs WHERE id=%s", (job_id,))
        job = await cur.fetchone()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job[0] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        await cur.execute("DELETE FROM jobs WHERE id=%s", (job_id,))
    conn.close()
    return {"message": "Job deleted successfully"}


@router.put("/close/{job_id}")
async def close_job(job_id: int, current_user=Depends(get_current_user)):
    require_role(current_user, ["employer"])
    conn = await get_db()
    async with conn.cursor() as cur:
        await cur.execute("SELECT user_id FROM jobs WHERE id=%s", (job_id,))
        job = await cur.fetchone()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job[0] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        await cur.execute("UPDATE jobs SET is_closed=1 WHERE id=%s", (job_id,))
    conn.close()
    return {"message": "Job closed successfully"}

# search 

@router.get("/search")
async def search_jobs(title: str = "", location: str = "", company: str = ""):
    conn = await get_db()
    async with conn.cursor(aiomysql.DictCursor) as cur:
        query = "SELECT * FROM jobs WHERE is_closed=0"
        params = []

        if title:
            query += " AND title LIKE %s"
            params.append(f"%{title}%")

        if location:
            query += " AND location LIKE %s"
            params.append(f"%{location}%")

        if company:
            query += " AND company LIKE %s"
            params.append(f"%{company}%")

        query += " ORDER BY created_at DESC"
        await cur.execute(query, params)
        jobs = await cur.fetchall()
    conn.close()
    return jobs

@router.get("/{id}")
async def search_jobs(id: int):
    conn = await get_db()
    async with conn.cursor(aiomysql.DictCursor) as cur:
        query = "SELECT * FROM jobs WHERE is_closed = 0 AND id = %s ORDER BY created_at DESC"
        await cur.execute(query, (id,))
        jobs = await cur.fetchone()
    conn.close()
    return jobs


@router.get("/job/{job_id}/applicants")
async def get_applicants(
    job_id: int,
    current_user=Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    name: str | None = None,
    skills: str | None = None,
    status: str | None = None,
):
    require_role(current_user, ["employer"])

    conn = await get_db()
    async with conn.cursor(aiomysql.DictCursor) as cur:
        # Verify job belongs to employer
        await cur.execute("SELECT user_id FROM jobs WHERE id=%s", (job_id,))
        job = await cur.fetchone()
        if not job or job["user_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Build query dynamically
        query = """
            SELECT a.id, u.id AS applicant_id, u.name, u.email, u.skills, u.bio, u.resume_url, a.status, a.applied_at
            FROM applications a
            JOIN users u ON a.user_id = u.id
            WHERE a.job_id=%s
        """
        params = [job_id]

        if name:
            query += " AND u.name LIKE %s"
            params.append(f"%{name}%")

        if skills:
            query += " AND u.skills LIKE %s"
            params.append(f"%{skills}%")

        if status:
            query += " AND a.status=%s"
            params.append(status)

        query += " ORDER BY a.applied_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        await cur.execute(query, params)
        applicants = await cur.fetchall()

        # Count total applicants for pagination
        count_query = "SELECT COUNT(*) AS total FROM applications a JOIN users u ON a.user_id=u.id WHERE a.job_id=%s"
        count_params = [job_id]
        if name:
            count_query += " AND u.name LIKE %s"
            count_params.append(f"%{name}%")
        if skills:
            count_query += " AND u.skills LIKE %s"
            count_params.append(f"%{skills}%")
        if status:
            count_query += " AND a.status=%s"
            count_params.append(status)
        await cur.execute(count_query, count_params)
        total = (await cur.fetchone())["total"]

    conn.close()
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "applicants": applicants
    }
