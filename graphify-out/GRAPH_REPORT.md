# Graph Report - issus(e)-tracker-LLM  (2026-05-12)

## Corpus Check
- 16 files · ~6,016 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 188 nodes · 303 edges · 23 communities (18 shown, 5 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 37 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `887f1340`
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
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]

## God Nodes (most connected - your core abstractions)
1. `WORKFLOW` - 18 edges
2. `PriorityEnum` - 12 edges
3. `Cache Retrieval Flow` - 11 edges
4. `ขั้นตอนการดึง cache แบบละเอียด` - 11 edges
5. `cache_lookup_node()` - 10 edges
6. `llm_predict_node()` - 10 edges
7. `Cache Lookup Node` - 9 edges
8. `LLM Predict Node` - 9 edges
9. `callback_node()` - 8 edges
10. `Semantic Cache` - 8 edges

## Surprising Connections (you probably didn't know these)
- `Semantic Cache` --rationale_for--> `Cache Lookup Node`  [INFERRED]
  CACHE.md → app/services/predict_agent/utils/node.py
- `Semantic Cache` --rationale_for--> `Save Cache Node`  [INFERRED]
  CACHE.md → app/services/predict_agent/utils/node.py
- `Semantic Cache` --references--> `Prediction Graph`  [EXTRACTED]
  CACHE.md → app/services/predict_agent/agent.py
- `Semantic Cache` --references--> `LLM Predict Node`  [EXTRACTED]
  CACHE.md → app/services/predict_agent/utils/node.py
- `Semantic Cache` --references--> `Load Cache Entries`  [EXTRACTED]
  CACHE.md → app/services/predict_agent/utils/cache.py

## Hyperedges (group relationships)
- **Ticket Prediction Workflow** — node_cache_lookup_node, node_llm_predict_node, node_save_cache_node, node_callback_node [EXTRACTED 1.00]
- **Deployment Services** — docker_compose_redis_service, docker_compose_app_service, docker_compose_worker_service [EXTRACTED 1.00]
- **Ticket State Models** — state_ticket_state, state_pending_ticket_item, state_indexed_ticket_predict_result, state_ticket_predict_result, state_hybrid_embedding_data [EXTRACTED 1.00]

## Communities (23 total, 5 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.13
Nodes (29): Prediction Graph, Build Redis URL, Build Ticket Cache Key, Calculate Weighted Similarity, Cosine Similarity, Find Best Cached Prediction, Get Dense Vector, Get Hybrid Embedding (+21 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (21): API Entry Flow, Cache Lookup Flow, Callback Flow, code:json ({), code:text (Backend), Configuration, Deployment Topology, End-to-End Sequence (+13 more)

### Community 2 - "Community 2"
Cohesion: 0.27
Nodes (15): BaseModel, Enum, companyData, formItem, predictRequest, predictResponse, PriorityEnum, Config (+7 more)

### Community 3 - "Community 3"
Cohesion: 0.12
Nodes (17): 10. ถ้ายังมี miss จะไปต่อที่ LLM, 1. เข้า `cache_lookup_node(state)`, 2. ดึง ticket จาก state ด้วย `_get_tickets_from_state()`, 3. โหลด cache ทั้งหมดจาก Redis ด้วย `load_cache_entries()`, 4. สร้าง embedding ของ ticket ปัจจุบันด้วย `get_ticket_embeddings()`, 5. หา cache ที่ใกล้ที่สุดด้วย `find_best_cached_prediction()`, 6. การอ่าน embedding จาก cache ด้วย `_get_dense_vector()`, 7. การคำนวณ similarity (+9 more)

### Community 4 - "Community 4"
Cohesion: 0.37
Nodes (14): str, _build_predict_messages(), _build_ticket_predict_result(), cache_lookup_node(), callback_node(), _extract_department_mapping(), get_department(), _get_tickets_from_state() (+6 more)

### Community 5 - "Community 5"
Cohesion: 0.12
Nodes (15): ภาพรวม, 1. เข้า `llm_predict_node()`, 2. เข้า `save_cache_node()`, สรุปหน้าที่ของแต่ละฟังก์ชัน, 3. map ticket เดิมกับผลลัพธ์ใหม่ด้วย `index`, สรุปสั้นที่สุด, 4. เรียก `save_prediction_cache(...)`, ค่าคงที่ของ cache (+7 more)

### Community 6 - "Community 6"
Cohesion: 0.15
Nodes (15): App Service, Redis Service, Worker Service, Health Endpoint, Normalize HMAC Signature, Verify HMAC, Verify Request HMAC, Verify Request HMAC Dependency (+7 more)

### Community 7 - "Community 7"
Cohesion: 0.35
Nodes (12): build_company_cache_index_key(), _build_redis_url(), build_ticket_cache_key(), calculate_weighted_similarity(), cosine_similarity(), find_best_cached_prediction(), _get_dense_vector(), get_hybrid_embedding() (+4 more)

### Community 8 - "Community 8"
Cohesion: 0.61
Nodes (6): generate_hmac(), _normalize_hmac_body(), normalize_hmac_signature(), verify_hmac(), verify_request_hmac(), verify_request_hmac_dependency()

### Community 9 - "Community 9"
Cohesion: 0.29
Nodes (6): AGENTS Instructions, Coding Style, Communication, Dependency Management, graphify, Rules

### Community 10 - "Community 10"
Cohesion: 0.47
Nodes (4): build_redis_url(), get_prediction_graph(), make_json_safe(), ticket_prediction()

## Knowledge Gaps
- **59 isolated node(s):** `Coding Style`, `Dependency Management`, `Communication`, `Rules`, `graphify` (+54 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `cache_lookup_node()` connect `Community 4` to `Community 2`, `Community 7`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Why does `generate_hmac()` connect `Community 8` to `Community 4`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `Prediction Graph` connect `Community 0` to `Community 6`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `PriorityEnum` (e.g. with `TicketItem` and `TicketPredictResult`) actually correct?**
  _`PriorityEnum` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `str` (e.g. with `make_json_safe()` and `ticket_prediction()`) actually correct?**
  _`str` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Coding Style`, `Dependency Management`, `Communication` to the rest of the system?**
  _59 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.13 - nodes in this community are weakly interconnected._