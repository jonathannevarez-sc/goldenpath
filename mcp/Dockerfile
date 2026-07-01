# Build from repo root: docker build -f mcp/Dockerfile -t goldenpath-mcp .
FROM python:3.12-slim

WORKDIR /app

RUN adduser --disabled-password --gecos "" mcpuser

COPY mcp/requirements.txt mcp/requirements.txt
RUN pip install --no-cache-dir -r mcp/requirements.txt

COPY mcp/goldenpath_mcp mcp/goldenpath_mcp
COPY cli/shop cli/shop
COPY skills skills
COPY docs docs
COPY templates/catalog.json templates/catalog.json
COPY templates templates

RUN chmod +x cli/shop

ENV GOLDENPATH_ROOT=/app
ENV MCP_TRANSPORT=streamable-http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8080
ENV GOLDENPATH_CHANNEL=stable
ENV GOLDENPATH_VERSION=v0.3.7

WORKDIR /app/mcp
EXPOSE 8080

USER mcpuser
CMD ["python", "-m", "goldenpath_mcp"]