FROM python:3.11-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy app code
COPY . .

# Prepare static files
RUN mkdir -p /app/staticfiles
RUN python manage.py collectstatic --noinput --clear

# Setup entrypoint
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8080
ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "tandem_backend.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "4"]

steps:
  # ... build and push steps ...

  # Step 3: Deploy to Cloud Run with Direct VPC Egress
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'tandem-backend-test'
      - '--image=gcr.io/$PROJECT_ID/tandem-backend:$SHORT_SHA'
      - '--region=europe-west3'
      - '--platform=managed'
      - '--network=webapp-vpc-test'
      - '--subnet=webapp-test-subnet-1'
      - '--network-interface=eth0'
      - '--memory=512Mi'
      - '--cpu=1'
      - '--timeout=3600'
      - '--update-secrets=DATABASE_URL=database-url:latest'
      - '--update-secrets=ALLOWED_HOSTS=allowed-hosts:latest'
      - '--update-secrets=SECRET_KEY=secret-key:latest'
      - '--set-env-vars=DEBUG=False'
      - '--allow-unauthenticated'