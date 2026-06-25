FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 
ENV UV_LINK_MODE=copy 

WORKDIR /src 

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

#COPY . /src
COPY . . 

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.13-slim-bookworm

WORKDIR /src

# Copy Virtual Environment from builder stage.
COPY --from=builder /src/.venv /src/.venv

# Copy Code 
COPY --from=builder /src/app /src/app
COPY --from=builder /src/proto /src/proto

# Place executables in the environment at the front of the path
ENV PATH="/src/.venv/bin:$PATH"
ENV DOCKER_RUNNING=1
ENV PYTHONUNBUFFERED=1

EXPOSE 50051

# Run the gRPC server.
CMD ["python", "-m", "app.grpc.server"]
