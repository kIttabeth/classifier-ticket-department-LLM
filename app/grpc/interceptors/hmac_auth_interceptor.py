# This module provides gRPC HMAC authentication for protected RPC methods.
import grpc

from app.core.config import settings
from app.utils.hmac import SIGNATURE_HEADER, verify_hmac


class HmacAuthInterceptor(grpc.ServerInterceptor):
    # Verify HMAC signatures from gRPC metadata before protected handlers run.

    def __init__(self, protected_methods: set[str] | None = None):
        # Store the full gRPC method names that require HMAC verification.
        self.protected_methods = protected_methods or {
            "/ticket_prediction.v1.TicketPredictionService/Predict"
        }

    def intercept_service(self, continuation, handler_call_details):
        # Wrap unary request handlers with metadata signature validation.
        handler = continuation(handler_call_details)
        if handler is None or handler_call_details.method not in self.protected_methods:
            return handler

        if handler.unary_unary is None:
            return handler

        def unary_unary_interceptor(request, context):
            # Reject missing or invalid HMAC signatures for deterministic protobuf bytes.
            metadata = dict(context.invocation_metadata())
            signature = metadata.get(SIGNATURE_HEADER.lower())
            if not signature:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, f"Missing {SIGNATURE_HEADER} metadata")

            body = request.SerializeToString(deterministic=True)
            if not verify_hmac(body=body, sig=signature, secret=settings.SECRET_API_KEY):
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid request signature")

            return handler.unary_unary(request, context)

        return grpc.unary_unary_rpc_method_handler(
            unary_unary_interceptor,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )
