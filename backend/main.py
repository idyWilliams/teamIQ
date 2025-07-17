from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import os
from contextlib import asynccontextmanager

from app.core.database import engine, Base
from app.api import auth, users, teams, projects, skills, tasks, notifications, integrations


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="iSentry TeamIQ",
    description="AI-Powered Intern & Team Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "http://localhost:3000", "http://localhost:5175", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(teams.router, prefix="/api/teams", tags=["Teams"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(skills.router, prefix="/api/skills", tags=["Skills"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["Integrations"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "iSentry TeamIQ API is running"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
