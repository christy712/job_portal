from fastapi import FastAPI
from app.routers import users, jobs, applications,auth
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Job Portal Backend")

origins = [
    "http://localhost:5173",  # React dev server
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(users.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(auth.router)