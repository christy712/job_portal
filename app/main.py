from fastapi import FastAPI
from app.routers import users, jobs, applications,auth

app = FastAPI(title="Job Portal Backend")

app.include_router(users.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(auth.router)