FROM python:3.11-slim

WORKDIR /workspace

COPY scripts/requirements-local-db.lock.txt /tmp/requirements.lock
RUN pip install --no-cache-dir -r /tmp/requirements.lock

COPY backend/ai/src /workspace/backend/ai/src
COPY backend/ai/fixtures /workspace/backend/ai/fixtures
COPY backend/ai/tests /workspace/backend/ai/tests
COPY docs/data-sources.json /workspace/docs/data-sources.json
COPY scripts /workspace/scripts

EXPOSE 8090
CMD ["python", "scripts/rag_dev_service.py"]
