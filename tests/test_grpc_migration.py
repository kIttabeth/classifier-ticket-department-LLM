# This module tests the gRPC ticket prediction API behavior.
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("BASE_BACKEND_URL", "http://callback.test")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("DENSE_EMBEDDING_BASE_URL", "http://embedding.test")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "0")
os.environ.setdefault("LANGSMITH_TRACING", "false")
os.environ.setdefault("SECRET_API_KEY", "test-secret")

import grpc

from app.grpc.generated import ticket_prediction_pb2
from app.grpc.generated import ticket_prediction_pb2_grpc
from app.grpc.mappers.ticket_prediction_mapper import proto_to_predict_request
from app.grpc.server import create_server
from app.schemas.predict_ticket_schema import companyData, formItem
from app.services.ticket_prediction_queue import queue_prediction_jobs
from app.utils.hmac import SIGNATURE_HEADER, generate_hmac


def build_proto_request() -> ticket_prediction_pb2.PredictRequest:
    # Build a protobuf request with repeated company/form data for adapter tests.
    return ticket_prediction_pb2.PredictRequest(
        data=[
            ticket_prediction_pb2.CompanyData(
                company_id="company-1",
                forms=[
                    ticket_prediction_pb2.FormItem(
                        id="form-a",
                        title="Bug",
                        description="App crashes",
                    ),
                    ticket_prediction_pb2.FormItem(
                        id="form-a",
                        title="Login",
                        description="Cannot sign in",
                    ),
                    ticket_prediction_pb2.FormItem(
                        id="form-b",
                        title="Billing",
                        description="Invoice is missing",
                    ),
                ],
            )
        ]
    )


class GrpcMigrationTests(unittest.TestCase):
    # Validate mapper, queueing, and gRPC HMAC behavior for the migration.

    def test_proto_to_predict_request_maps_existing_dto_shape(self):
        # Ensure protobuf requests map to the internal DTO shape.
        dto = proto_to_predict_request(build_proto_request())

        self.assertEqual(dto.data[0].company_id, "company-1")
        self.assertEqual(len(dto.data[0].forms), 3)
        self.assertEqual(dto.data[0].forms[0].title, "Bug")

    @patch("app.services.ticket_prediction_queue.ticket_prediction.delay")
    def test_queue_prediction_jobs_groups_by_company_and_form(self, delay_mock):
        # Ensure prediction requests enqueue the expected grouped Celery state shape.
        response = queue_prediction_jobs(
            [
                companyData(
                    company_id="company-1",
                    forms=[
                        formItem(id="form-a", title="Bug", description="App crashes"),
                        formItem(id="form-a", title="Login", description="Cannot sign in"),
                        formItem(id="form-b", title="Billing", description="Invoice is missing"),
                    ],
                )
            ]
        )

        self.assertEqual(response.message, "Processing queued")
        self.assertEqual(response.queued_count, 2)
        self.assertEqual(delay_mock.call_count, 2)
        first_state = delay_mock.call_args_list[0].args[0]
        self.assertEqual(first_state["company_id"], "company-1")
        self.assertEqual(first_state["form_id"], "form-a")
        self.assertEqual(len(first_state["grouped_tickets"]), 2)
        self.assertIn("thread_id", first_state)

    def test_grpc_health_does_not_require_hmac(self):
        # Ensure operational health checks can call the gRPC server without auth metadata.
        server = create_server()
        port = server.add_insecure_port("localhost:0")
        server.start()
        try:
            with grpc.insecure_channel(f"localhost:{port}") as channel:
                stub = ticket_prediction_pb2_grpc.TicketPredictionServiceStub(channel)
                response = stub.Health(ticket_prediction_pb2.HealthRequest())
        finally:
            server.stop(0)

        self.assertEqual(response.status, "ok")

    @patch("app.services.ticket_prediction_queue.ticket_prediction.delay")
    def test_grpc_predict_requires_valid_hmac(self, delay_mock):
        # Ensure Predict rejects missing auth and accepts a valid deterministic protobuf HMAC.
        server = create_server()
        port = server.add_insecure_port("localhost:0")
        server.start()
        try:
            with grpc.insecure_channel(f"localhost:{port}") as channel:
                stub = ticket_prediction_pb2_grpc.TicketPredictionServiceStub(channel)
                request = build_proto_request()

                with self.assertRaises(grpc.RpcError) as missing_error:
                    stub.Predict(request)
                self.assertEqual(missing_error.exception.code(), grpc.StatusCode.UNAUTHENTICATED)

                signature = generate_hmac(
                    request.SerializeToString(deterministic=True),
                    os.environ["SECRET_API_KEY"],
                )
                response = stub.Predict(
                    request,
                    metadata=[(SIGNATURE_HEADER.lower(), f"sha256={signature}")],
                )
        finally:
            server.stop(0)

        self.assertEqual(response.message, "Processing queued")
        self.assertEqual(response.queued_count, 2)
        self.assertEqual(delay_mock.call_count, 2)


if __name__ == "__main__":
    unittest.main()
