FROM python:3.11-slim

WORKDIR /app

# Build with internal_hackathon as the Docker context. The backend imports the
# pure adapter/identity-consent/scoring/copilot packages, so they are copied into the same image
# rather than relying on sibling paths that do not exist in a Render container.
COPY services/backend/requirements.txt /tmp/backend-requirements.txt
RUN pip install --no-cache-dir -r /tmp/backend-requirements.txt

COPY libs/adapters /app/libs/adapters
COPY libs/identity-consent /app/libs/identity-consent
COPY services/scoring-engine /app/services/scoring-engine
COPY services/ai-copilot /app/services/ai-copilot
COPY services/backend /app/services/backend

RUN pip install --no-cache-dir -e /app/libs/adapters -e /app/libs/identity-consent -e /app/services/scoring-engine -e /app/services/backend

WORKDIR /app/services/backend
EXPOSE 8000
# Render supplies PORT (10000 by default); local Docker falls back to 8000.
# Apply the checked-in schema before serving traffic. This keeps a Render
# redeploy from exposing an API whose SQLAlchemy models are ahead of Supabase.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
