from fastapi import APIRouter

router = APIRouter(tags=["healthcheck"])

@router.get("/health")
def health():
    return {"status": "ok","service":"LLM"}