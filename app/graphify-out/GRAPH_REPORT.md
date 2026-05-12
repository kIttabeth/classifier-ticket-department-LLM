# Graph Report - app  (2026-05-07)

## Corpus Check
- 12 files · ~3,328 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 66 nodes · 128 edges · 12 communities (10 shown, 2 thin omitted)
- Extraction: 74% EXTRACTED · 26% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.73)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `38dd3135`
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
- [[_COMMUNITY_Community 8|Community 8]]

## God Nodes (most connected - your core abstractions)
1. `PriorityEnum` - 11 edges
2. `cache_lookup_node()` - 9 edges
3. `llm_predict_node()` - 9 edges
4. `callback_node()` - 7 edges
5. `save_prediction_cache()` - 5 edges
6. `_get_tickets_from_state()` - 5 edges
7. `get_department()` - 5 edges
8. `PendingTicketItem` - 5 edges
9. `IndexedTicketPredictResult` - 5 edges
10. `generate_hmac()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `predict_ticket()` --calls--> `predictResponse`  [INFERRED]
  routes/v1/endpoints/predict.py → schemas/predict_ticket_schema.py
- `Config` --uses--> `PriorityEnum`  [INFERRED]
  services/predict_agent/utils/state.py → schemas/predict_ticket_schema.py
- `get_department()` --calls--> `generate_hmac()`  [INFERRED]
  services/predict_agent/utils/node.py → utils/hmac.py
- `callback_node()` --calls--> `generate_hmac()`  [INFERRED]
  services/predict_agent/utils/node.py → utils/hmac.py
- `get_redis_client()` --calls--> `build_redis_url()`  [INFERRED]
  services/predict_agent/utils/cache.py → worker.py

## Communities (12 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.24
Nodes (13): build_redis_url(), build_company_cache_index_key(), build_ticket_cache_key(), calculate_weighted_similarity(), cosine_similarity(), find_best_cached_prediction(), _get_dense_vector(), get_hybrid_embedding() (+5 more)

### Community 1 - "Community 1"
Cohesion: 0.34
Nodes (12): str, _build_predict_messages(), _build_ticket_predict_result(), cache_lookup_node(), callback_node(), _extract_department_mapping(), get_department(), _get_tickets_from_state() (+4 more)

### Community 2 - "Community 2"
Cohesion: 0.31
Nodes (10): Enum, PriorityEnum, Config, HybridEmbeddingData, IndexedTicketPredictResult, PendingTicketItem, TicketItem, TicketPredictResult (+2 more)

### Community 3 - "Community 3"
Cohesion: 0.52
Nodes (6): generate_hmac(), _normalize_hmac_body(), normalize_hmac_signature(), verify_hmac(), verify_request_hmac(), verify_request_hmac_dependency()

### Community 4 - "Community 4"
Cohesion: 0.53
Nodes (5): BaseModel, companyData, formItem, predictRequest, predictResponse

### Community 5 - "Community 5"
Cohesion: 0.83
Nodes (3): get_prediction_graph(), make_json_safe(), ticket_prediction()

## Knowledge Gaps
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `cache_lookup_node()` connect `Community 1` to `Community 0`, `Community 2`?**
  _High betweenness centrality (0.169) - this node is a cross-community bridge._
- **Why does `generate_hmac()` connect `Community 3` to `Community 1`?**
  _High betweenness centrality (0.147) - this node is a cross-community bridge._
- **Why does `PriorityEnum` connect `Community 2` to `Community 1`, `Community 4`?**
  _High betweenness centrality (0.141) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `PriorityEnum` (e.g. with `TicketItem` and `TicketPredictResult`) actually correct?**
  _`PriorityEnum` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `str` (e.g. with `make_json_safe()` and `ticket_prediction()`) actually correct?**
  _`str` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `cache_lookup_node()` (e.g. with `load_cache_entries()` and `get_ticket_embeddings()`) actually correct?**
  _`cache_lookup_node()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `llm_predict_node()` (e.g. with `PendingTicketItem` and `IndexedTicketPredictResult`) actually correct?**
  _`llm_predict_node()` has 3 INFERRED edges - model-reasoned connections that need verification._