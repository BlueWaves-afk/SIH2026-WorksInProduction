FROM python:3.11-slim

WORKDIR /app

# Build with internal_hackathon as the Docker context. The backend imports the
# pure adapter/scoring/copilot packages, so they are copied into the same image
# rather than relying on sibling paths that do not exist in a Render container.
COPY services/backend/requirements.txt /tmp/backend-requirements.txt
RUN pip install --no-cache-dir -r /tmp/backend-requirements.txt

COPY libs/adapters /app/libs/adapters
COPY services/scoring-engine /app/services/scoring-engine
COPY services/ai-copilot /app/services/ai-copilot
COPY services/backend /app/services/backend

RUN pip install --no-cache-dir -e /app/libs/adapters -e /app/services/scoring-engine -e /app/services/backend

WORKDIR /app/services/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
