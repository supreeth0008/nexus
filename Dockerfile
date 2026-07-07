# I build Nexus as a distroless container
FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml README.md ./
COPY nexus ./nexus
RUN pip install --no-cache-dir --prefix=/install .
FROM gcr.io/distroless/python3-debian12
COPY --from=builder /install /usr/local
WORKDIR /workspace
ENTRYPOINT ["nexus"]
CMD ["--help"]
LABEL org.opencontainers.image.source="https://github.com/supreeth0008/nexus"
LABEL org.opencontainers.image.description="Nexus autonomous infrastructure control plane"
