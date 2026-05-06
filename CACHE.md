# Cache Retrieval Flow

เอกสารนี้อธิบายการทำงานของระบบ cache ในส่วน `predict_agent` แบบละเอียด โดยเน้น flow การ "ดึง cache" เป็นหลัก และปิดท้ายด้วย flow ตอนบันทึก cache กลับเข้า Redis เพื่อให้เห็นภาพครบทั้งวงจร

## ภาพรวม

ระบบนี้ใช้ **semantic cache** ไม่ใช่ cache ที่ดูแค่ `title` และ `description` ต้องตรง 100% เท่านั้น  
แนวคิดคือ:

1. รับ ticket เข้ามา
2. สร้าง embedding ของ `title` และ `description`
3. โหลด cache ที่มีอยู่ใน Redis
4. เอา embedding ของ ticket ใหม่ไปเทียบกับ embedding ที่เก็บใน cache
5. ถ้าคะแนนความคล้ายสูงพอ ให้ใช้ผลลัพธ์จาก cache ทันที
6. ถ้าไม่เจอ cache ที่คล้ายพอ ค่อยส่ง ticket นั้นไปให้ LLM ทำนาย
7. ผลลัพธ์ใหม่จาก LLM จะถูกบันทึกกลับเข้า cache เพื่อใช้รอบถัดไป

ตัวแปรสำคัญอยู่ใน [app/services/predict_agent/utils/cache.py](/d:/python%20learn/issus(e)-tracker-LLM/app/services/predict_agent/utils/cache.py) และ node ที่เรียกใช้อยู่ใน [app/services/predict_agent/utils/node.py](/d:/python%20learn/issus(e)-tracker-LLM/app/services/predict_agent/utils/node.py)

## จุดเริ่มต้นของ flow

graph ถูกประกอบไว้ใน [app/services/predict_agent/agent.py](/d:/python%20learn/issus(e)-tracker-LLM/app/services/predict_agent/agent.py)

ลำดับการทำงานคือ:

1. `cache_lookup`
2. ถ้ามี ticket ที่ยังหา cache ไม่เจอ ไป `llm_predict`
3. จากนั้นไป `save_cache`
4. สุดท้ายไป `callback_node`

ดังนั้นจุดที่ "ดึง cache" จริง ๆ เริ่มจากฟังก์ชัน `cache_lookup_node()`

## โครงสร้าง state ที่เกี่ยวกับ cache

อยู่ใน [app/services/predict_agent/utils/state.py](/d:/python%20learn/issus(e)-tracker-LLM/app/services/predict_agent/utils/state.py)

สิ่งสำคัญมี 4 ตัว:

- `HybridEmbeddingData`
เก็บ embedding ของข้อความ 1 ชิ้น โดยมี
`dense`: เวกเตอร์ตัวเลขสำหรับใช้คำนวณ similarity
`sparse`: โครงสร้าง sparse embedding ที่ API ส่งกลับมา

- `PendingTicketItem`
เก็บ ticket ที่ยัง cache miss และต้องส่งต่อไปให้ LLM  
นอกจาก `title` กับ `description` แล้ว ยังเก็บ `title_embedding` และ `description_embedding` ไว้ด้วย เพื่อไม่ต้องเรียก embedding ซ้ำตอนเซฟ cache

- `cached_results`
เป็น list ของ `IndexedTicketPredictResult` สำหรับ ticket ที่หา cache เจอแล้ว

- `uncached_tickets`
เป็น list ของ `PendingTicketItem` สำหรับ ticket ที่ยังไม่เจอ cache และต้องทำนายใหม่

## ค่าคงที่ของ cache

อยู่ใน [app/services/predict_agent/utils/cache.py](/d:/python%20learn/issus(e)-tracker-LLM/app/services/predict_agent/utils/cache.py)

- `CACHE_KEY_PREFIX = "ticket_prediction_cache"`
ใช้เป็น prefix ของ key จริงใน Redis

- `CACHE_INDEX_KEY = "ticket_prediction_cache:keys"`
เป็น Redis set ที่เก็บรายการ key ของ cache ทุกตัวไว้รวมกัน  
ระบบใช้ set นี้เป็น index เพื่อรู้ว่าต้องไปอ่าน key ไหนบ้าง

- `CACHE_TTL_SECONDS = 60 * 60 * 24 * 7`
อายุ cache 7 วัน

- `CACHE_THRESHOLD = 0.9`
คะแนน similarity ขั้นต่ำที่ถือว่า cache นี้ "ใกล้พอ" จะนำมาใช้ได้

- `TITLE_WEIGHT = 0.4`
- `DESCRIPTION_WEIGHT = 0.6`
ตอนรวมคะแนน similarity จะให้น้ำหนัก description มากกว่า title

## ขั้นตอนการดึง cache แบบละเอียด

### 1. เข้า `cache_lookup_node(state)`

ฟังก์ชันนี้อยู่ใน [app/services/predict_agent/utils/node.py](/d:/python%20learn/issus(e)-tracker-LLM/app/services/predict_agent/utils/node.py)

หน้าที่หลักคือ:

1. ตรวจว่า state ก่อนหน้ามี error หรือไม่
2. ดึงรายการ ticket จาก state
3. โหลด cache ทั้งหมดจาก Redis
4. วนทีละ ticket เพื่อหา cache ที่ใกล้ที่สุด
5. แยกผลเป็น `cached_results` และ `uncached_tickets`

ถ้า state ก่อนหน้าพังอยู่แล้ว ฟังก์ชันนี้จะไม่ทำงานต่อ และคืน error ทันที

### 2. ดึง ticket จาก state ด้วย `_get_tickets_from_state()`

ฟังก์ชันนี้ช่วยอ่าน ticket จาก state ให้รองรับหลายรูปแบบ

ลำดับคือ:

1. ถ้า `state.grouped_tickets` มีข้อมูล ให้ใช้ list นี้
2. ถ้าไม่มี แต่มี `title` และ `description` แบบเดิมใน state ก็จะ wrap เป็น ticket เดียว
3. ถ้าไม่มีทั้งคู่ จะถือว่าไม่มี ticket และคืน error

สรุปคือมันเป็นตัว normalize input ให้ `cache_lookup_node()` ทำงานกับ ticket list ได้สม่ำเสมอ

### 3. โหลด cache ทั้งหมดจาก Redis ด้วย `load_cache_entries()`

ฟังก์ชันนี้อยู่ใน [app/services/predict_agent/utils/cache.py](/d:/python%20learn/issus(e)-tracker-LLM/app/services/predict_agent/utils/cache.py)

ลำดับการทำงาน:

1. เรียก `get_redis_client()`
2. `get_redis_client()` จะคืน Redis client แบบ shared
3. ถ้ายังไม่เคยมี client มาก่อน จะสร้างจาก `Redis.from_url(...)`
4. URL ของ Redis ถูกสร้างโดย `_build_redis_url()` จากค่า host, port, db และ password ใน settings

หลังจากได้ client แล้ว:

1. เรียก `smembers(CACHE_INDEX_KEY)` เพื่ออ่าน set ของ key ทั้งหมด
2. สร้าง list ว่างชื่อ `cache_entries`
3. วนทุก `cache_key`
4. เรียก `get(cache_key)` เพื่อดึง JSON payload ของ cache แต่ละตัว

กรณีที่เจอข้อมูลผิดปกติ:

- ถ้า key ยังอยู่ใน set แต่ค่าใน Redis หายไปแล้ว
ระบบจะ `srem` key นั้นออกจาก index set ทันที

- ถ้าอ่านค่าได้ แต่ `json.loads(...)` ไม่ผ่าน
ระบบจะลบทั้ง key จริงด้วย `delete(cache_key)` และลบออกจาก set ด้วย `srem(...)`

ผลลัพธ์สุดท้ายของ `load_cache_entries()` คือ list ของ dict ที่ parse JSON แล้วและพร้อมถูกนำไปเทียบ similarity

### 4. สร้าง embedding ของ ticket ปัจจุบันด้วย `get_ticket_embeddings()`

ใน `cache_lookup_node()` หลังโหลด cache แล้ว ระบบจะวนทีละ ticket และเรียก:

`get_ticket_embeddings(title, description)`

ฟังก์ชันนี้ทำ 2 อย่าง:

1. เรียก `get_hybrid_embedding(title)`
2. เรียก `get_hybrid_embedding(description)`

แล้วคืนค่าเป็น tuple:

- `title_embedding`
- `description_embedding`

#### `get_hybrid_embedding()` ทำอะไร

ฟังก์ชันนี้ยิง HTTP POST ไปที่:

`{settings.DENSE_EMBEDDING_BASE_URL}/hybrid_embedding`

body ที่ส่งคือ:

```json
{
  "content": "ข้อความที่ต้องการ embedding"
}
```

จากนั้นระบบจะ:

1. ตรวจว่า response status สำเร็จหรือไม่ด้วย `raise_for_status()`
2. อ่าน JSON
3. ดึง `dense`
4. ดึง `sparse`
5. แปลงให้อยู่ในรูป `HybridEmbeddingData`

ถ้า response shape ไม่ถูกต้อง เช่น `dense` ไม่ใช่ list จะ raise error ทันที

### 5. หา cache ที่ใกล้ที่สุดด้วย `find_best_cached_prediction()`

นี่คือฟังก์ชันหลักของ semantic cache matching

input ของมันคือ:

- `cache_entries`: รายการ cache ทั้งหมดจาก Redis
- `title_embedding`: embedding ของ title ปัจจุบัน
- `description_embedding`: embedding ของ description ปัจจุบัน

ผลลัพธ์คือ tuple:

- `best_result`: `TicketPredictResult | None`
- `best_score`: `float`

#### ภายใน `find_best_cached_prediction()` ทำอะไรบ้าง

1. ตั้งต้น `best_score = 0.0`
2. ตั้งต้น `best_result = None`
3. วนทุก `cache_entry`
4. ดึง `title_embedding` และ `description_embedding` ที่เก็บอยู่ใน cache entry
5. เรียก `calculate_weighted_similarity(...)`
6. ถ้าคะแนนมากกว่า threshold และมากกว่าคะแนนที่ดีที่สุดเดิม ให้แทนค่าเป็น candidate ใหม่
7. เมื่อวนครบ จะคืน result ที่ดีที่สุดกลับไป

### 6. การอ่าน embedding จาก cache ด้วย `_get_dense_vector()`

ฟังก์ชันนี้เป็นตัวช่วยเล็ก ๆ แต่สำคัญมาก

เหตุผลที่มีฟังก์ชันนี้เพราะ cache เก่าและ cache ใหม่อาจเก็บ embedding คนละรูปแบบ:

- แบบใหม่: dict เช่น `{ "dense": [...], "sparse": {...} }`
- แบบเก่า: list ตรง ๆ เช่น `[0.12, 0.87, ...]`

`_get_dense_vector()` จะพยายามอ่านให้ได้เป็น `list[float]` เสมอ  
ถ้าอ่านไม่ได้จะคืน `[]`

สรุปคือมันช่วยเรื่อง backward compatibility ของข้อมูล cache

### 7. การคำนวณ similarity

มี 2 ชั้น:

#### `cosine_similarity(left_vector, right_vector)`

หน้าที่:

1. เช็กว่าทั้งสองเวกเตอร์มีข้อมูลไหม
2. เช็กว่าความยาวเท่ากันไหม
3. คำนวณ dot product
4. คำนวณ magnitude ของแต่ละฝั่ง
5. คืนค่า cosine similarity

กรณีที่คำนวณไม่ได้ เช่น vector ว่างหรือยาวไม่เท่ากัน จะคืน `0.0`

#### `calculate_weighted_similarity(...)`

หน้าที่:

1. คำนวณ similarity ของ title
2. คำนวณ similarity ของ description
3. รวมคะแนนตามน้ำหนัก

สูตรคือ:

```text
(0.4 * title_similarity) + (0.6 * description_similarity)
```

เพราะระบบให้ความสำคัญกับรายละเอียดใน description มากกว่า title

### 8. ตัดสินว่าเป็น cache hit หรือ miss

หลังจาก `find_best_cached_prediction()` คืนค่ากลับมา `cache_lookup_node()` จะตัดสินดังนี้:

- ถ้า `cached_result is not None`
ถือว่า cache hit  
จะ append เข้า `cached_results` พร้อม `index` เดิมของ ticket

- ถ้า `cached_result is None`
ถือว่า cache miss  
จะสร้าง `PendingTicketItem` แล้ว append เข้า `uncached_tickets`

จุดสำคัญคือ `PendingTicketItem` จะเก็บ embedding ที่เพิ่งสร้างไว้ด้วย เพื่อใช้ต่อใน `save_cache_node()` โดยไม่ต้องคำนวณใหม่

### 9. ถ้า hit ทั้งหมด จะจบตั้งแต่ node นี้

ถ้า `uncached_tickets` ว่าง แปลว่า ticket ทุกใบหา cache เจอหมด

ระบบจะ:

1. เรียก `_merge_indexed_results(...)`
2. เอา `cached_results` มาเรียงกลับตาม index เดิม
3. ใส่ผลลัพธ์ลง `data`

จากนั้น `route_after_cache_lookup()` จะส่ง flow ไป `callback_node` ทันที โดยไม่เรียก LLM เลย

### 10. ถ้ายังมี miss จะไปต่อที่ LLM

ถ้า `uncached_tickets` ไม่ว่าง:

1. `cache_lookup_node()` จะคืน `cached_results` และ `uncached_tickets`
2. `route_after_cache_lookup()` จะคืน `"llm_predict"`
3. graph จะส่งต่อไป `llm_predict_node()`

ตรงนี้คือจุดที่ cache ช่วยลดงาน LLM ได้ เพราะส่งต่อเฉพาะ ticket ที่ไม่ผ่าน threshold เท่านั้น

## รูปแบบข้อมูลที่เก็บใน cache

ตอนเซฟ ระบบใช้ `save_prediction_cache()` ใน [app/services/predict_agent/utils/cache.py](/d:/python%20learn/issus(e)-tracker-LLM/app/services/predict_agent/utils/cache.py)

payload ที่เก็บใน Redis มีหน้าตาประมาณนี้:

```json
{
  "title": "Printer cannot connect",
  "description": "Office printer disconnects every morning",
  "title_embedding": {
    "dense": [0.1, 0.2, 0.3],
    "sparse": {}
  },
  "description_embedding": {
    "dense": [0.4, 0.5, 0.6],
    "sparse": {}
  },
  "result": {
    "title": "Printer cannot connect",
    "description": "Office printer disconnects every morning",
    "priority": "medium",
    "department_name": "IT Support"
  },
  "created_at": "2026-05-03T00:00:00+00:00"
}
```

## วิธีตั้งชื่อ key ใน Redis

ใช้ `build_ticket_cache_key(title, description)`

ลำดับคือ:

1. เอา `title` กับ `description` มาทำเป็น JSON
2. ใช้ `sort_keys=True` เพื่อให้ format คงที่
3. hash ด้วย `sha256`
4. เติม prefix เป็น `ticket_prediction_cache:<digest>`

แม้ตอน "ดึง cache" จะไม่ได้ lookup ด้วย key นี้โดยตรง แต่ key นี้ใช้ตอนบันทึก cache ใหม่ เพื่อให้ข้อมูล ticket เดิมมี key คงที่

## Flow ตอน save cache กลับเข้า Redis

แม้คำขอหลักคือเรื่องการดึง cache แต่ส่วนนี้สำคัญเพราะอธิบายว่าข้อมูลใน cache มาจากไหน

### 1. เข้า `llm_predict_node()`

ticket ที่อยู่ใน `uncached_tickets` จะถูกส่งไปให้ LLM ทำนายผล  
ผลลัพธ์จะถูกเก็บใน `fresh_results`

### 2. เข้า `save_cache_node()`

ฟังก์ชันนี้จะทำงานเฉพาะกรณีที่:

- state ยัง success
- มี `fresh_results`
- มี `uncached_tickets`

ถ้าไม่มีผลใหม่ จะ skip

### 3. map ticket เดิมกับผลลัพธ์ใหม่ด้วย `index`

`save_cache_node()` สร้าง `pending_ticket_map = {ticket.index: ticket}`

เหตุผลคือ:

- `fresh_results` มีผลทำนาย
- `uncached_tickets` มี embedding เดิม

ระบบต้องเอาสองชุดนี้มาประกบกันเพื่อเซฟเป็น cache entry ที่สมบูรณ์

### 4. เรียก `save_prediction_cache(...)`

ฟังก์ชันนี้จะ:

1. สร้าง key ด้วย `build_ticket_cache_key(...)`
2. สร้าง payload
3. `set(...)` ลง Redis พร้อม `ex=CACHE_TTL_SECONDS`
4. `sadd(CACHE_INDEX_KEY, cache_key)` เพื่อเพิ่ม key ลง index set
5. `expire(CACHE_INDEX_KEY, CACHE_TTL_SECONDS)` เพื่อยืดอายุ index set ให้สอดคล้องกับ cache

ดังนั้นรอบต่อไป `load_cache_entries()` ก็จะอ่าน key ตัวนี้เจอและนำมาเทียบ similarity ได้ทันที

## สรุปหน้าที่ของแต่ละฟังก์ชัน

- `_build_redis_url()`
ประกอบ Redis URL จาก settings

- `get_redis_client()`
คืน Redis client แบบ shared

- `build_ticket_cache_key(title, description)`
สร้าง key คงที่สำหรับ cache 1 รายการ

- `get_hybrid_embedding(content)`
เรียก embedding service เพื่อสร้าง dense และ sparse embedding

- `get_ticket_embeddings(title, description)`
สร้าง embedding แยกสำหรับ title และ description

- `cosine_similarity(left_vector, right_vector)`
คำนวณ cosine similarity ระหว่างเวกเตอร์ 2 ชุด

- `calculate_weighted_similarity(...)`
รวม similarity ของ title และ description ตามน้ำหนัก 0.4/0.6

- `_get_dense_vector(embedding_payload)`
อ่าน dense vector จาก cache payload ได้ทั้งรูปแบบใหม่และเก่า

- `load_cache_entries()`
โหลด cache ทั้งหมดจาก Redis และล้างข้อมูลเสียระหว่างทาง

- `find_best_cached_prediction(...)`
หา cache entry ที่ similarity สูงสุดและผ่าน threshold

- `save_prediction_cache(...)`
บันทึกผลลัพธ์ใหม่พร้อม embedding ลง Redis

- `cache_lookup_node(state)`
node หลักที่แยก cache hit กับ cache miss

- `route_after_cache_lookup(state)`
ตัดสินว่าจะไป callback เลย หรือไป LLM ต่อ

- `save_cache_node(state)`
บันทึกผลจาก LLM กลับเข้า semantic cache

## สรุปสั้นที่สุด

ระบบนี้ไม่ได้ถาม Redis ว่า "มี key นี้ไหม" แล้วจบ  
แต่ถามว่า "ใน cache ทั้งหมด มี ticket ไหนที่ความหมายใกล้กับ ticket ใหม่มากพอไหม"

ถ้าใกล้พอ:

- ใช้ผลเดิมจาก cache
- ไม่ต้องเรียก LLM

ถ้าไม่ใกล้พอ:

- ส่งไปทำนายใหม่
- แล้วบันทึกผลนั้นกลับเข้า cache เพื่อใช้ในอนาคต
