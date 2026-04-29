# This module groups versioned API routers and route-level protections.
from fastapi import APIRouter, Depends

from app.routes.v1.endpoints import health, predict
from app.utils.hmac import verify_request_hmac_dependency

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(
    predict.router,
    dependencies=[Depends(verify_request_hmac_dependency)],
)
