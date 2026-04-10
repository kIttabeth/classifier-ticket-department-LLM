from fastapi import FastAPI
from app.routes.v1.router import api_router

app = FastAPI(title="Classifier-Ticket-Department-LLM",version="1.0.0")

app.include_router(api_router,prefix="/api/v1")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
