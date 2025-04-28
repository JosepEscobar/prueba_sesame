from fastapi import APIRouter
from app.api.v1.endpoints import agents

api_router = APIRouter()

api_router.include_router(
    agents.router,
    prefix="/agents",
    tags=["agents"]
) 