FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=7860
ENV HOST=0.0.0.0
ENV WORKERS=1

EXPOSE 7860

CMD ["sh", "-c", "uvicorn bug_triage_env.server:app --host $HOST --port $PORT --workers $WORKERS"]
