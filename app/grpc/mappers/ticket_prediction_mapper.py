# This module maps between protobuf ticket prediction messages and Pydantic DTOs.
from app.grpc.generated import ticket_prediction_pb2
from app.schemas.predict_ticket_schema import companyData, formItem, predictRequest, predictResponse


def proto_to_predict_request(request: ticket_prediction_pb2.PredictRequest) -> predictRequest:
    # Convert a protobuf prediction request into the existing Pydantic DTO.
    return predictRequest(
        data=[
            companyData(
                company_id=company.company_id,
                forms=[
                    formItem(
                        id=form.id,
                        title=form.title,
                        description=form.description,
                    )
                    for form in company.forms
                ],
            )
            for company in request.data
        ]
    )


def predict_response_to_proto(response: predictResponse) -> ticket_prediction_pb2.PredictResponse:
    # Convert the existing Pydantic response into a protobuf response.
    return ticket_prediction_pb2.PredictResponse(
        message=response.message,
        queued_count=response.queued_count,
    )
