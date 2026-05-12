# This module provides Redis-backed semantic cache helpers for ticket prediction.
import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from redis.asyncio import Redis

from app.core.config import settings
from app.services.predict_agent.utils.state import HybridEmbeddingData, TicketPredictResult
from app.worker import build_redis_url

CACHE_KEY_PREFIX = "ticket_prediction_cache"
CACHE_TTL_SECONDS = 60 * 60 * 24 * 7
CACHE_THRESHOLD = 0.9
TITLE_WEIGHT = 0.4
DESCRIPTION_WEIGHT = 0.6

_redis_client: Optional[Redis] = None


async def get_redis_client() -> Redis:
    # Return a shared async Redis client.
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(build_redis_url(), decode_responses=True)
    return _redis_client


def build_company_cache_index_key(company_id: str) -> str:
    # Create the Redis set key that tracks cache entries for one company.
    return f"{CACHE_KEY_PREFIX}:keys:{company_id}"


def build_ticket_cache_key(company_id: str, title: str, description: str) -> str:
    # Create a stable Redis key for one company-scoped ticket cache entry.
    raw_value = json.dumps(
        {"company_id": company_id, "title": title, "description": description},
        ensure_ascii=False,
        sort_keys=True,
    )
    digest = hashlib.sha256(raw_value.encode("utf-8")).hexdigest()
    return f"{CACHE_KEY_PREFIX}:{digest}"


async def get_hybrid_embedding(content: str) -> HybridEmbeddingData:
    # Fetch dense and sparse embeddings from the configured hybrid embedding API.
    embedding_url = f"{settings.DENSE_EMBEDDING_BASE_URL.rstrip('/')}/hybrid_embedding"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            embedding_url,
            json={"content": content},
        )
        response.raise_for_status()
        embedding_payload = response.json()
        if not isinstance(embedding_payload, dict):
            raise ValueError("Unsupported embedding response format")

        dense_vector = embedding_payload.get("dense", [])
        sparse_vector = embedding_payload.get("sparse", {})

        if not isinstance(dense_vector, list):
            raise ValueError("Embedding response missing dense vector")
        if not isinstance(sparse_vector, dict):
            sparse_vector = {}

        return HybridEmbeddingData(
            dense=[float(value) for value in dense_vector],
            sparse=sparse_vector,
        )


async def get_ticket_embeddings(title: str, description: str) -> tuple[HybridEmbeddingData, HybridEmbeddingData]:
    # Fetch title and description embeddings for one ticket.
    title_embedding = await get_hybrid_embedding(title)
    description_embedding = await get_hybrid_embedding(description)
    return title_embedding, description_embedding


def cosine_similarity(left_vector: list[float], right_vector: list[float]) -> float:
    # Calculate cosine similarity for two vectors.
    if not left_vector or not right_vector or len(left_vector) != len(right_vector):
        return 0.0

    dot_product = sum(left * right for left, right in zip(left_vector, right_vector))
    left_magnitude = math.sqrt(sum(value * value for value in left_vector))
    right_magnitude = math.sqrt(sum(value * value for value in right_vector))

    if left_magnitude == 0 or right_magnitude == 0:
        return 0.0

    return dot_product / (left_magnitude * right_magnitude)


def calculate_weighted_similarity(
    query_title_embedding: list[float],
    query_description_embedding: list[float],
    cached_title_embedding: list[float],
    cached_description_embedding: list[float],
) -> float:
    # Combine title and description similarity scores with the requested weights.
    title_similarity = cosine_similarity(query_title_embedding, cached_title_embedding)
    description_similarity = cosine_similarity(query_description_embedding, cached_description_embedding)
    return (TITLE_WEIGHT * title_similarity) + (DESCRIPTION_WEIGHT * description_similarity)


def _get_dense_vector(embedding_payload: Any) -> list[float]:
    # Read a dense vector from either the new object shape or older list-based cache entries.
    if isinstance(embedding_payload, dict):
        dense_vector = embedding_payload.get("dense", [])
        if isinstance(dense_vector, list):
            return [float(value) for value in dense_vector]
        return []

    if isinstance(embedding_payload, list):
        return [float(value) for value in embedding_payload]

    return []


async def load_cache_entries(company_id: str) -> list[dict[str, Any]]:
    # Load all currently available semantic cache entries for one company from Redis.
    redis_client = await get_redis_client()
    cache_index_key = build_company_cache_index_key(company_id)
    cache_keys = await redis_client.smembers(cache_index_key)
    cache_entries: list[dict[str, Any]] = []

    for cache_key in cache_keys:
        cache_payload = await redis_client.get(cache_key)
        if not cache_payload:
            await redis_client.srem(cache_index_key, cache_key)
            continue

        try:
            cache_entry = json.loads(cache_payload)
            if cache_entry.get("company_id") not in (None, "", company_id):
                continue
            cache_entries.append(cache_entry)
        except json.JSONDecodeError:
            await redis_client.delete(cache_key)
            await redis_client.srem(cache_index_key, cache_key)

    return cache_entries


def find_best_cached_prediction(
    cache_entries: list[dict[str, Any]],
    title_embedding: HybridEmbeddingData,
    description_embedding: HybridEmbeddingData,
) -> tuple[Optional[TicketPredictResult], float]:
    # Find the best cached prediction that passes the semantic similarity threshold.
    best_score = 0.0
    best_result: Optional[TicketPredictResult] = None

    for cache_entry in cache_entries:
        cached_title_embedding = cache_entry.get("title_embedding", {})
        cached_description_embedding = cache_entry.get("description_embedding", {})
        score = calculate_weighted_similarity(
            query_title_embedding=title_embedding.dense,
            query_description_embedding=description_embedding.dense,
            cached_title_embedding=_get_dense_vector(cached_title_embedding),
            cached_description_embedding=_get_dense_vector(cached_description_embedding),
        )

        if score >= CACHE_THRESHOLD and score > best_score:
            best_score = score
            best_result = TicketPredictResult.model_validate(cache_entry.get("result", {}))

    return best_result, best_score


async def save_prediction_cache(
    company_id: str,
    title: str,
    description: str,
    title_embedding: HybridEmbeddingData,
    description_embedding: HybridEmbeddingData,
    result: TicketPredictResult,
) -> None:
    # Save one prediction result and its embeddings into Redis with one-week TTL.
    redis_client = await get_redis_client()
    cache_index_key = build_company_cache_index_key(company_id)
    cache_key = build_ticket_cache_key(company_id=company_id, title=title, description=description)
    cache_payload = {
        "company_id": company_id,
        "title": title,
        "description": description,
        "title_embedding": title_embedding.model_dump(mode="json"),
        "description_embedding": description_embedding.model_dump(mode="json"),
        "result": result.model_dump(mode="json"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    await redis_client.set(cache_key, json.dumps(cache_payload, ensure_ascii=False), ex=CACHE_TTL_SECONDS)
    await redis_client.sadd(cache_index_key, cache_key)
    await redis_client.expire(cache_index_key, CACHE_TTL_SECONDS)
