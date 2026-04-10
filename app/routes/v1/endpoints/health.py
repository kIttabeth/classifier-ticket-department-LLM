from fastapi import APIRouter

router = APIRouter(prefix="/health",tags=["healthcheck"])

@router.get("/")
def health():
    return {"status": "ok","service":"LLM"}