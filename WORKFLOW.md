# This module documents the end-to-end runtime workflow of the project.

# WORKFLOW

## Overview

โปรเจกต์นี้เป็นระบบรับ ticket จาก backend, ส่งงานเข้า queue, ประมวลผลด้วย LangGraph + LLM, ใช้ Redis เป็นทั้ง Celery broker/backend และ semantic cache แล้ว callback ผลลัพธ์กลับไปที่ backend ต้นทาง

องค์ประกอบหลักมี 3 service:

- `app`: FastAPI รับคำขอที่ `POST /api/v1/predict-LLM`
- `worker`: Celery worker สำหรับประมวลผล prediction แบบ async
- `redis`: ใช้เป็น queue/result backend ของ Celery และเก็บ semantic cache

## High-Level Flow

1. Backend เรียก `POST /api/v1/predict-LLM`
2. FastAPI ตรวจ `X-HMAC-Signature` ก่อนเข้า endpoint
3. Endpoint จัดกลุ่ม tickets ตาม `(company_id, form_id)`
4. แต่ละกลุ่มถูกส่งเข้า Celery task `ticket_prediction`
5. Worker โหลด LangGraph prediction flow
6. Graph เริ่มจาก `cache_lookup_node`
7. ถ้า cache hit ครบทุก ticket จะข้าม LLM ไป callback ทันที
8. ถ้ายังมี cache miss จะไป `llm_predict_node`
9. ผลที่ LLM ทำนายใหม่จะถูกบันทึกใน Redis ผ่าน `save_cache_node`
10. `callback_node` ส่งผลลัพธ์กลับ backend ด้วย HMAC signature

## API Entry Flow

ไฟล์ที่เกี่ยวข้อง:

- [app/main.py](/D:/python%20learn/issus(e)-tracker-LLM/app/main.py)
- [app/routes/v1/router.py](/D:/python%20learn/issus(e)-tracker-LLM/app/routes/v1/router.py)
- [app/routes/v1/endpoints/predict.py](/D:/python%20learn/issus(e)-tracker-LLM/app/routes/v1/endpoints/predict.py)
- [app/utils/hmac.py](/D:/python%20learn/issus(e)-tracker-LLM/app/utils/hmac.py)

ลำดับการทำงาน:

1. `app.main` สร้าง FastAPI app และ mount router ที่ prefix `/api/v1`
2. `api_router` ผูก route `predict.router` พร้อม dependency `verify_request_hmac_dependency`
3. ทุกคำขอเข้า `POST /predict-LLM` ต้องมี header `X-HMAC-Signature`
4. `verify_request_hmac()` อ่าน raw body แล้วตรวจ HMAC ด้วย `SECRET_API_KEY`
5. ถ้า signature ไม่ถูกต้อง ระบบจะตอบ `401 Unauthorized`
6. ถ้าผ่าน validation endpoint `predict_ticket()` จะเริ่มจัดกลุ่มงาน

## Request Shape

ไฟล์ schema:

- [app/schemas/predict_ticket_schema.py](/D:/python%20learn/issus(e)-tracker-LLM/app/schemas/predict_ticket_schema.py)

request มีรูปแบบหลักดังนี้:

```json
{
  "data": [
    {
      "company_id": "company_1",
      "forms": [
        {
          "id": "form_a",
          "title": "Login error",
          "description": "User cannot sign in"
        }
      ]
    }
  ]
}
```

endpoint จะตอบกลับทันทีด้วย:

- `message`: สถานะการ queue งาน
- `queued_count`: จำนวนกลุ่ม `(company_id, form_id)` ที่ถูกส่งเข้า worker

## Grouping and Queueing

ใน [app/routes/v1/endpoints/predict.py](/D:/python%20learn/issus(e)-tracker-LLM/app/routes/v1/endpoints/predict.py):

- ระบบวน `tickets.data`
- แตก `forms` ออกมา
- group ตาม key `(company_id, form.id)`
- แปลงแต่ละ form เป็น `{title, description}`
- สร้าง `state_dict` ต่อหนึ่งกลุ่ม
- ใส่ `thread_id` แบบ unique ด้วย `uuid`
- เรียก `ticket_prediction.delay(state_dict)`

ผลคือ 1 Celery task จะรับผิดชอบ 1 company + 1 form + รายการ tickets ในกลุ่มนั้น

## Worker Runtime

ไฟล์หลัก:

- [app/worker.py](/D:/python%20learn/issus(e)-tracker-LLM/app/worker.py)

หน้าที่ของ worker:

- สร้าง Redis URL กลางด้วย `build_redis_url()`
- ใช้ Redis URL เดียวกันกับ Celery broker/backend
- สร้าง process-level asyncio event loop เพื่อใช้ซ้ำข้าม task
- โหลด prediction graph แบบ lazy ผ่าน `get_prediction_graph()`
- รัน `graph.ainvoke(state_dict, {"configurable": {"thread_id": thread_id}})`
- ถ้า task ล้มเหลวจะ retry ได้สูงสุด 2 ครั้ง โดยหน่วง 15 วินาที

หมายเหตุ:

- การ lazy import graph ช่วยเลี่ยง circular import ระหว่าง worker กับ cache module
- บน Windows worker ถูกตั้งค่าให้ใช้ `solo` pool เพื่อเลี่ยงปัญหา process model

## Prediction Graph

ไฟล์หลัก:

- [app/services/predict_agent/agent.py](/D:/python%20learn/issus(e)-tracker-LLM/app/services/predict_agent/agent.py)
- [app/services/predict_agent/utils/node.py](/D:/python%20learn/issus(e)-tracker-LLM/app/services/predict_agent/utils/node.py)
- [app/services/predict_agent/utils/state.py](/D:/python%20learn/issus(e)-tracker-LLM/app/services/predict_agent/utils/state.py)

graph มี 4 node:

1. `cache_lookup`
2. `llm_predict`
3. `save_cache`
4. `callback_node`

เส้นทาง:

- `START -> cache_lookup`
- ถ้า cache hit ครบทั้งหมด: `cache_lookup -> callback_node`
- ถ้ามี miss: `cache_lookup -> llm_predict -> save_cache -> callback_node -> END`

`TicketState` เป็น state กลางของ graph โดยเก็บ:

- ข้อมูล input เช่น `company_id`, `form_id`, `grouped_tickets`
- ผลลัพธ์ cache เช่น `cached_results`
- ผลลัพธ์ใหม่จาก LLM เช่น `fresh_results`
- tickets ที่ยังไม่เจอ cache เช่น `uncached_tickets`
- ผลลัพธ์สุดท้ายใน `data`
- สถานะการทำงานใน `success`, `error`, `steps`

## Cache Lookup Flow

logic อยู่ใน:

- [app/services/predict_agent/utils/node.py](/D:/python%20learn/issus(e)-tracker-LLM/app/services/predict_agent/utils/node.py)
- [app/services/predict_agent/utils/cache.py](/D:/python%20learn/issus(e)-tracker-LLM/app/services/predict_agent/utils/cache.py)

ลำดับการทำงานของ `cache_lookup_node()`:

1. อ่าน tickets จาก `state.grouped_tickets`
2. โหลด cache ทั้งหมดจาก Redis ผ่าน `load_cache_entries()`
3. สำหรับ ticket แต่ละตัว เรียก `get_ticket_embeddings(title, description)`
4. คำนวณ similarity เทียบกับ cached entries ด้วย `find_best_cached_prediction()`
5. ถ้าคะแนนมากกว่าหรือเท่ากับ `CACHE_THRESHOLD = 0.9` ถือว่า hit
6. ถ้า hit เก็บลง `cached_results`
7. ถ้า miss เก็บลง `uncached_tickets` พร้อม embedding ที่คำนวณแล้ว
8. ถ้า hit ครบทุก ticket จะ merge ผลลัพธ์เป็น `data` และจบ flow ฝั่ง LLM

รายละเอียด cache:

- key prefix: `ticket_prediction_cache`
- index set: `ticket_prediction_cache:keys`
- TTL: 7 วัน
- similarity:
  - title weight = `0.4`
  - description weight = `0.6`

## LLM Prediction Flow

logic อยู่ใน [app/services/predict_agent/utils/node.py](/D:/python%20learn/issus(e)-tracker-LLM/app/services/predict_agent/utils/node.py)

`llm_predict_node()` ทำงานดังนี้:

1. เรียก `get_department(company_id)` ไป backend เพื่อดึงรายการแผนก
2. สร้าง prompt ต่อ ticket ด้วย `_build_predict_messages()`
3. ใช้ `ChatGoogleGenerativeAI` model `gemini-2.5-flash`
4. บังคับ structured output ด้วย `TicketRoutingDecision`
5. LLM คืนเฉพาะ field routing คือ `priority` และ `department_name`
6. ระบบประกอบ `TicketPredictResult` จาก `title` และ `description` ของ input ticket เดิม แล้วใส่ค่า routing จาก LLM
7. merge `cached_results` กับ `fresh_results` กลับไปเป็น `data` ตาม index เดิม

กฎเชิงธุรกิจสำคัญ:

- ถ้า title/description ไม่ใช่ recommendation request หรือ issue report, prompt ระบุให้คืน `priority = null` และ `department_name = null`
- กรณี title/description ไม่พอให้วิเคราะห์ ระบบจะถือเป็นผลลัพธ์ valid แบบ no-routing ได้เช่นกัน โดย `priority` และ `department_name` เป็น `null`
- `title` และ `description` ในผลลัพธ์สุดท้ายไม่ได้มาจาก LLM แต่ยึดจาก input เดิมเสมอ เพื่อกัน parse error จาก structured output
- department ที่เลือกควรมาจากรายการ `Available Departments` ที่ backend ส่งกลับมา

## Save Cache Flow

`save_cache_node()` ทำงานหลัง LLM เฉพาะกรณีที่มี `fresh_results`

ลำดับการทำงาน:

1. map `uncached_tickets` ตาม `index`
2. วน `fresh_results`
3. เรียก `save_prediction_cache(...)`
4. บันทึก title, description, embeddings, result, created_at ลง Redis
5. อัปเดต index set และ TTL

จุดสำคัญคือ cache เก็บ embedding ของทั้ง title และ description ไว้ด้วย เพื่อให้ request รอบถัดไปค้นแบบ semantic similarity ได้ ไม่ใช่แค่ exact match

## Callback Flow

`callback_node()` เป็นขั้นสุดท้ายของ graph

ลำดับการทำงาน:

1. ถ้า state ผิดพลาด จะสร้าง payload failed จาก input tickets เดิม
2. ถ้าสำเร็จ จะตรวจว่ามี field routing จริงหรือไม่
3. ถ้าไม่มี `priority` และ `department_name` ในทุก item จะ skip callback
4. ถ้ามี routing result จะเรียก `get_department(company_id)` อีกครั้งเพื่อ map `department_name -> department_id`
5. สร้าง payload สำหรับ backend
6. sign payload ด้วย `generate_hmac()`
7. ส่ง `POST {BASE_BACKEND_URL}/api/v1/create-bulk`
8. บันทึกผลตอบกลับไว้ใน `callback_response`

payload ฝั่ง callback มีข้อมูลหลัก:

- `department_id`
- `form_id`
- `title`
- `description`
- `priority`
- `status`
- `message`

## Redis Responsibilities

Redis ถูกใช้ 2 บทบาทพร้อมกัน:

1. Celery broker/backend
2. Semantic cache storage

ในปัจจุบัน Redis connection URL ถูกประกอบที่ [app/worker.py](/D:/python%20learn/issus(e)-tracker-LLM/app/worker.py) และ `cache.py` เรียกใช้ผ่าน `build_redis_url()` เพื่อให้ worker กับ cache ใช้แหล่ง config เดียวกัน

## Configuration

ไฟล์:

- [app/core/config.py](/D:/python%20learn/issus(e)-tracker-LLM/app/core/config.py)

runtime settings หลัก:

- `BASE_BACKEND_URL`
- `GEMINI_API_KEY`
- `DENSE_EMBEDDING_BASE_URL`
- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_DB`
- `SECRET_API_KEY`
- `LANGSMITH_TRACING`

ค่าพวกนี้ถูกโหลดด้วย `pydantic-settings`

## Deployment Topology

ไฟล์:

- [docker-compose.yaml](/D:/python%20learn/issus(e)-tracker-LLM/docker-compose.yaml)

service layout:

- `redis`
  - เปิด port `6379`
  - มี healthcheck `redis-cli ping`
- `app`
  - เปิด port `8080`
  - depends on `redis`
  - healthcheck `GET /api/v1/health`
- `worker`
  - รัน `celery -A app.worker.celery_app worker`
  - depends on `redis`
  - restart `unless-stopped`

## Failure Handling

จุดจัดการ error หลัก:

- HMAC ไม่ผ่าน: API ตอบ `401`
- endpoint error ตอน queue: API ตอบ `500`
- graph node error: เขียนลง `state.error` และ `steps`
- worker task error: Celery retry สูงสุด 2 รอบ
- callback ล้มเหลว: บันทึกสถานะ failed ใน `callback_response`
- cache entry เสีย format: `load_cache_entries()` จะลบ entry ที่เสียออกจาก Redis

## End-to-End Sequence

```text
Backend
  -> FastAPI /api/v1/predict-LLM
  -> HMAC verification
  -> Group by (company_id, form_id)
  -> Celery delay(state_dict)
  -> Redis broker
  -> Celery worker
  -> LangGraph cache_lookup
     -> Redis semantic cache
     -> Embedding service
  -> LangGraph llm_predict (only cache misses)
     -> Backend departments API
     -> Gemini model
  -> LangGraph save_cache
     -> Redis semantic cache
  -> LangGraph callback_node
     -> Backend create-bulk API
```

## File Map

- `app/main.py`: FastAPI app entrypoint
- `app/routes/v1/router.py`: รวม routes และ security dependency
- `app/routes/v1/endpoints/predict.py`: endpoint รับงานและส่งเข้า queue
- `app/worker.py`: Celery worker และ Redis setup กลาง
- `app/services/predict_agent/agent.py`: สร้าง LangGraph
- `app/services/predict_agent/utils/node.py`: business workflow ของแต่ละ node
- `app/services/predict_agent/utils/cache.py`: semantic cache utilities
- `app/services/predict_agent/utils/state.py`: state models ของ graph
- `app/utils/hmac.py`: HMAC sign/verify helpers
- `docker-compose.yaml`: runtime topology ของ services
