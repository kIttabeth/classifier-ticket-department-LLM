# This module implements the gRPC ticket prediction service adapter.
import grpc

from app.grpc.generated import ticket_prediction_pb2
from app.grpc.generated import ticket_prediction_pb2_grpc
from app.grpc.mappers.ticket_prediction_mapper import proto_to_predict_request, predict_response_to_proto
from app.services.ticket_prediction_queue import queue_prediction_jobs


class TicketPredictionServicer(ticket_prediction_pb2_grpc.TicketPredictionServiceServicer):
    # Adapt gRPC calls to the existing ticket prediction queueing workflow.

    def Predict(self, request, context):
        # Queue prediction jobs from a protobuf request and return queue status.
        try:
            dto_request = proto_to_predict_request(request)
            dto_response = queue_prediction_jobs(dto_request.data)
            return predict_response_to_proto(dto_response)
        except Exception as exc:
            context.abort(grpc.StatusCode.INTERNAL, str(exc))

    def Health(self, request, context):
        # Return a lightweight health response for gRPC runtime checks.
        return ticket_prediction_pb2.HealthResponse(status="ok")
