"""V1 API router — aggregates all v1 endpoint routers."""

from fastapi import APIRouter

from solexplorer.api.v1.token_analyse import router as token_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(token_router)
