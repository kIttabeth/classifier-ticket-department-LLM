from celery import Celery
import asyncio
import os

from app.core.config import settings
from app.services.predict_agent.agent import graph

_redis_pass = getattr(settings, "REDIS_PASSWORD", None)

if _redis_pass:
    REDIS_URL = f"redis://:{_redis_pass}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
else:
    REDIS_URL = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
    
print(f"[Worker] Connecting to Redis at: {REDIS_URL}")

celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

is_windows = os.name == "nt"

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Bangkok",
    enable_utc=True,
    # Task timeout: 30 minutes max per job
    task_time_limit=1800, #Kill error
    task_soft_time_limit=None if is_windows else 1500, # Soft timeout ไม่รองรับบน Windows
    # Worker concurrency
    worker_pool="solo" if is_windows else "prefork",  # prefork บน Windows ทำให้เกิด WinError 5 ได้
    worker_concurrency=1 if is_windows else None,
    worker_prefetch_multiplier=1,  # One task at a time per worker (important for heavy LLM/embedding jobs)
    task_acks_late=True,  # Acknowledge tasks after completion to avoid losing tasks on worker failure
    worker_max_tasks_per_child=10,  # Restart worker after 10 tasks to prevent memory leaks
)

# Keep one process-level event loop for Celery tasks. Using asyncio.run per task
# closes the loop after each run and can cause "Event loop is closed" on reused async clients.
_event_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_event_loop)

@celery_app.task(name="ticket_prediction",bind=True,max_retries=2)
def ticket_prediction(self, state_dict:dict):
    try:
        company_id = state_dict.get("company_id", "")
        form_id = state_dict.get("form_id", "")
        thread_id = state_dict.get("thread_id", f"{company_id}_{form_id}" if company_id and form_id else None)

        global _event_loop
        if _event_loop.is_closed():
            _event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_event_loop)

        return _event_loop.run_until_complete(
            graph.ainvoke(
                state_dict,
                {"configurable": {"thread_id": thread_id}},
            )
        )
    
    except Exception as e:
        print("Worker error:", str(e))
        raise self.retry(exc=e, countdown=15)