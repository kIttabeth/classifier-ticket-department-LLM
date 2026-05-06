# Graph Report - ca30848454824d  (2026-05-06)

## Corpus Check
- 15 files · ~4,668 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 161 nodes · 266 edges · 22 communities (17 shown, 5 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a44b642e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]

## God Nodes (most connected - your core abstractions)
1. `PriorityEnum` - 11 edges
2. `Cache Retrieval Flow` - 11 edges
3. `ขั้นตอนการดึง cache แบบละเอียด` - 11 edges
4. `cache_lookup_node()` - 10 edges
5. `llm_predict_node()` - 9 edges
6. `Cache Lookup Node` - 9 edges
7. `LLM Predict Node` - 9 edges
8. `callback_node()` - 8 edges
9. `Semantic Cache` - 8 edges
10. `Prediction Graph` - 8 edges

## Surprising Connections (you probably didn't know these)
- `Semantic Cache` --references--> `Prediction Graph`  [EXTRACTED]
  CACHE.md → app/services/predict_agent/agent.py
- `Semantic Cache` --rationale_for--> `Cache Lookup Node`  [INFERRED]
  CACHE.md → app/services/predict_agent/utils/node.py
- `Semantic Cache` --rationale_for--> `Save Cache Node`  [INFERRED]
  CACHE.md → app/services/predict_agent/utils/node.py
- `Semantic Cache` --references--> `LLM Predict Node`  [EXTRACTED]
  CACHE.md → app/services/predict_agent/utils/node.py
- `Semantic Cache` --references--> `Load Cache Entries`  [EXTRACTED]
  CACHE.md → app/services/predict_agent/utils/cache.py

## Hyperedges (group relationships)
- **Ticket Prediction Workflow** — node_cache_lookup_node, node_llm_predict_node, node_save_cache_node, node_callback_node [EXTRACTED 1.00]
- **Deployment Services** — docker_compose_redis_service, docker_compose_app_service, docker_compose_worker_service [EXTRACTED 1.00]
- **Ticket State Models** — state_ticket_state, state_pending_ticket_item, state_indexed_ticket_predict_result, state_ticket_predict_result, state_hybrid_embedding_data [EXTRACTED 1.00]

## Communities (22 total, 5 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.13
Nodes (27): Build Redis URL, Build Ticket Cache Key, Calculate Weighted Similarity, Cosine Similarity, Find Best Cached Prediction, Get Dense Vector, Get Hybrid Embedding, Get Redis Client (+19 more)

### Community 1 - "Community 1"
Cohesion: 0.29
Nodes (14): BaseModel, Enum, companyData, formItem, predictRequest, predictResponse, PriorityEnum, Config (+6 more)

### Community 2 - "Community 2"
Cohesion: 0.12
Nodes (17): 10. ถ้ายังมี miss จะไปต่อที่ LLM, 1. เข้า `cache_lookup_node(state)`, 2. ดึง ticket จาก state ด้วย `_get_tickets_from_state()`, 3. โหลด cache ทั้งหมดจาก Redis ด้วย `load_cache_entries()`, 4. สร้าง embedding ของ ticket ปัจจุบันด้วย `get_ticket_embeddings()`, 5. หา cache ที่ใกล้ที่สุดด้วย `find_best_cached_prediction()`, 6. การอ่าน embedding จาก cache ด้วย `_get_dense_vector()`, 7. การคำนวณ similarity (+9 more)

### Community 3 - "Community 3"
Cohesion: 0.14
Nodes (17): Prediction Graph, App Service, Redis Service, Worker Service, Health Endpoint, Normalize HMAC Signature, Verify HMAC, Verify Request HMAC (+9 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): ภาพรวม, 1. เข้า `llm_predict_node()`, 2. เข้า `save_cache_node()`, สรุปหน้าที่ของแต่ละฟังก์ชัน, 3. map ticket เดิมกับผลลัพธ์ใหม่ด้วย `index`, สรุปสั้นที่สุด, 4. เรียก `save_prediction_cache(...)`, ค่าคงที่ของ cache (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.43
Nodes (12): str, _build_predict_messages(), cache_lookup_node(), callback_node(), _extract_department_mapping(), get_department(), _get_tickets_from_state(), llm_predict_node() (+4 more)

### Community 6 - "Community 6"
Cohesion: 0.37
Nodes (11): _build_redis_url(), build_ticket_cache_key(), calculate_weighted_similarity(), cosine_similarity(), find_best_cached_prediction(), _get_dense_vector(), get_hybrid_embedding(), get_redis_client() (+3 more)

### Community 7 - "Community 7"
Cohesion: 0.61
Nodes (6): generate_hmac(), _normalize_hmac_body(), normalize_hmac_signature(), verify_hmac(), verify_request_hmac(), verify_request_hmac_dependency()

### Community 8 - "Community 8"
Cohesion: 0.29
Nodes (6): AGENTS Instructions, Coding Style, Communication, Dependency Management, graphify, Rules

### Community 9 - "Community 9"
Cohesion: 0.5
Nodes (3): build_redis_url(), get_prediction_graph(), ticket_prediction()

## Knowledge Gaps
- **41 isolated node(s):** `Coding Style`, `Dependency Management`, `Communication`, `Rules`, `graphify` (+36 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `cache_lookup_node()` connect `Community 5` to `Community 1`, `Community 6`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `Prediction Graph` connect `Community 3` to `Community 0`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `generate_hmac()` connect `Community 7` to `Community 5`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `PriorityEnum` (e.g. with `TicketItem` and `TicketPredictResult`) actually correct?**
  _`PriorityEnum` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `cache_lookup_node()` (e.g. with `load_cache_entries()` and `get_ticket_embeddings()`) actually correct?**
  _`cache_lookup_node()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Coding Style`, `Dependency Management`, `Communication` to the rest of the system?**
  _41 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.13 - nodes in this community are weakly interconnected._