# Ticket Prediction gRPC API

The service exposes ticket prediction through gRPC only.

The contract lives in `proto/ticket_prediction.proto` and exposes `TicketPredictionService.Predict` plus `Health`.

Run the gRPC server locally:

```bash
python -m app.grpc.server
```

`Predict` queues one Celery job per company/form group. Clients must send `x-hmac-signature` metadata where the signature is the HMAC SHA-256 digest of the deterministic serialized `PredictRequest` protobuf bytes. `Health` is unauthenticated so runtime checks can call it directly.
