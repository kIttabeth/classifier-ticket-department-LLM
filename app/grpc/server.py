# This module starts the standalone gRPC server for ticket prediction.
from concurrent import futures
import os

import grpc

from app.grpc.generated import ticket_prediction_pb2_grpc
from app.grpc.interceptors.hmac_auth_interceptor import HmacAuthInterceptor
from app.grpc.services.ticket_prediction_service import TicketPredictionServicer


def create_server() -> grpc.Server:
    # Create and configure the gRPC server with service adapters and interceptors.
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[HmacAuthInterceptor()],
    )
    ticket_prediction_pb2_grpc.add_TicketPredictionServiceServicer_to_server(
        TicketPredictionServicer(),
        server,
    )
    return server


def serve() -> None:
    # Start the gRPC server and block until it terminates.
    port = int(os.getenv("GRPC_PORT", "50051"))
    server = create_server()
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"[gRPC] TicketPredictionService listening on port {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
