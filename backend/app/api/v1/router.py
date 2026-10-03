"""
API v1 Router — aggregates all endpoint modules.

Each feature has its own router file and is included with appropriate
prefixes and tags for OpenAPI documentation.
"""

from fastapi import APIRouter

from app.api.v1 import auth, jobs, candidates, applications, resumes
from app.api.v1 import interviews, offers, dashboard, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(candidates.router, prefix="/candidates", tags=["Candidates"])
api_router.include_router(applications.router, prefix="/applications", tags=["Applications"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["Resumes"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["Interviews"])
api_router.include_router(offers.router, prefix="/offers", tags=["Offers"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
