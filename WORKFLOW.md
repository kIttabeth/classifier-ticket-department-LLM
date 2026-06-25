# Ticket Prediction gRPC Workflow

This project exposes ticket prediction through gRPC only. The gRPC server accepts prediction requests, validates HMAC metadata for `Predict`, queues grouped jobs into Celery, and the worker runs the existing LangGraph prediction workflow.

## Runtime Services

- `grpc`: runs `python -m app.grpc.server` on port `50051`
- `worker`: runs `celery -A app.worker.celery_app worker`
- `redis`: stores Celery broker/backend data and semantic cache data

## Request Flow

1. A client calls `ticket_prediction.v1.TicketPredictionService/Predict`.
2. `app.grpc.interceptors.hmac_auth_interceptor.HmacAuthInterceptor` verifies `x-hmac-signature` metadata against deterministic protobuf request bytes.
3. `app.grpc.services.ticket_prediction_service.TicketPredictionServicer` maps the protobuf request to the existing internal DTO shape.
4. `app.services.ticket_prediction_queue.queue_prediction_jobs()` groups tickets by `(company_id, form_id)`.
5. Each group is queued through `ticket_prediction.delay(state_dict)`.
6. `app.worker.ticket_prediction()` invokes the LangGraph prediction graph with the original state shape.
7. The graph performs cache lookup, LLM prediction when needed, cache save, and callback handling.

## gRPC Contract

The protobuf contract is defined in `proto/ticket_prediction.proto`.

```proto
service TicketPredictionService {
  rpc Predict(PredictRequest) returns (PredictResponse);
  rpc Health(HealthRequest) returns (HealthResponse);
}
```

`Predict` returns:

```json
{
  "message": "Processing queued",
  "queued_count": 1
}
```

`Health` returns:

```json
{
  "status": "ok"
}
```

## HMAC

`Predict` requires `x-hmac-signature` metadata. The signature is an HMAC SHA-256 digest of:

```python
request.SerializeToString(deterministic=True)
```

The server accepts plain hex, `sha=<hex>`, or `sha256=<hex>` signatures.

## Internal State Shape

Celery still receives the existing `state_dict` shape:

```python
{
    "company_id": company_id,
    "form_id": form_id,
    "grouped_tickets": [
        {
            "title": title,
            "description": description,
        }
    ],
    "thread_id": thread_id,
}
```

Keeping this state shape isolates transport changes from the LangGraph workflow.
