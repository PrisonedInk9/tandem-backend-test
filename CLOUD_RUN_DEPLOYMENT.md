# Cloud Run Deployment Guide

## Prerequisites
- Google Cloud project with billing enabled
- gcloud CLI installed and authenticated
- Cloud SQL instance (PostgreSQL 15) in same VPC
- VPC connector created in the same region

## Setup Steps

### 1. Create Cloud SQL Secrets
Store sensitive values in Google Cloud Secret Manager:

```bash
# Set variables
export PROJECT_ID=your-project-id
export REGION=europe-west1
export SECRET_KEY="your-django-secret-key-here"
export DB_PASSWORD="your-postgres-password"
export CLOUD_SQL_INSTANCE="projects/YOUR_PROJECT/instances/YOUR_INSTANCE"

# Create SECRET_KEY secret
echo -n "$SECRET_KEY" | gcloud secrets create tandem-secret-key --data-file=-

# Create DATABASE_URL secret
# For Cloud SQL proxy socket (recommended):
echo -n "postgresql:///tandem_db?host=/cloudsql/$CLOUD_SQL_INSTANCE" | gcloud secrets create tandem-database-url --data-file=-

# Or for private IP (if using Private IP):
echo -n "postgresql://tandem_user:$DB_PASSWORD@PRIVATE_IP:5432/tandem_db" | gcloud secrets create tandem-database-url --data-file=-
```

### 2. Create Kubernetes Secret (if using kubectl)
```bash
kubectl create secret generic tandem-secrets \
  --from-literal=secret-key="$SECRET_KEY" \
  --from-literal=database-url="postgresql:///tandem_db?host=/cloudsql/$CLOUD_SQL_INSTANCE"
```

### 3. Build and Push Image
```bash
# Set variables
export PROJECT_ID=your-project-id
export IMAGE_NAME=tandem-backend

# Build
docker build -t gcr.io/$PROJECT_ID/$IMAGE_NAME:latest .

# Push to Container Registry
docker push gcr.io/$PROJECT_ID/$IMAGE_NAME:latest
```

### 4. Deploy to Cloud Run (gcloud CLI)
```bash
gcloud run deploy tandem-backend \
  --image gcr.io/$PROJECT_ID/tandem-backend:latest \
  --platform managed \
  --region europe-west1 \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10 \
  --min-instances 1 \
  --vpc-connector projects/$PROJECT_ID/locations/europe-west1/connectors/YOUR_CONNECTOR \
  --set-env-vars DEBUG=False,ALLOWED_HOSTS=tandem-backend.run.app \
  --set-secrets SECRET_KEY=tandem-secret-key:latest,DATABASE_URL=tandem-database-url:latest \
  --allow-unauthenticated
```

### 5. Alternative: Deploy using kubectl + cloud-run-service.yaml
Before applying, update the manifest with your values:

```bash
# Edit cloud-run-service.yaml
# Replace:
#   - gcr.io/PROJECT_ID/ → gcr.io/your-project-id/
#   - REGION → us-central1
#   - CONNECTOR_NAME → your-vpc-connector-name
#   - YOUR_CUSTOM_DOMAIN.com → your domain

kubectl apply -f cloud-run-service.yaml
```

### 6. Configure Custom Domain (Optional)
```bash
gcloud run domain-mappings create \
  --service tandem-backend \
  --domain your-domain.com \
  --platform managed \
  --region us-central1
```

### 7. Run Django Migrations (First Time)
After deployment, run migrations on the Cloud SQL database:

```bash
# Get the Cloud Run service URL
export SERVICE_URL=$(gcloud run services describe tandem-backend --platform managed --region europe-west1 --format='value(status.url)')

# Or use the Cloud SQL proxy locally to run migrations:
cloud_sql_proxy -instances=PROJECT_ID:REGION:INSTANCE_NAME &
python manage.py migrate --settings=tandem_backend.settings
```

## Environment Variables

**Required in Cloud Run:**
- `DEBUG=False` (production setting)
- `SECRET_KEY` — Django secret key (use Secret Manager)
- `ALLOWED_HOSTS` — comma-separated domain list
- `DATABASE_URL` — Cloud SQL connection string (use Secret Manager)

## Database Connection Options

### Option 1: Cloud SQL Proxy Socket (RECOMMENDED)
```
postgresql:///tandem_db?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
```
- Most secure
- No exposed database password
- Automatic SSL encryption
- Requires VPC connector or Cloud SQL Proxy sidecar

### Option 2: Private IP
```
postgresql://username:password@PRIVATE_IP:5432/tandem_db
```
- Requires VPC connector in same VPC as Cloud SQL
- Credentials in connection string (use Secret Manager)

### Option 3: Public IP (NOT RECOMMENDED)
```
postgresql://username:password@PUBLIC_IP:5432/tandem_db
```
- Only use for testing
- Database must be publicly accessible
- Security risk

## VPC Connector Setup
If not already created:

```bash
gcloud compute networks vpc-access connectors create YOUR_CONNECTOR \
  --network=default \
  --region=europe-west1 \
  --min-instances=2 \
  --max-instances=10
```

## Monitoring

```bash
# View logs
gcloud run services describe tandem-backend --platform managed --region us-central1

# Stream logs
gcloud alpha run services logs read tandem-backend --region europe-west1 --follow

# View metrics
gcloud run services describe tandem-backend --platform managed --region europe-west1 --format=json
```

## Troubleshooting

**Connection timeout to Cloud SQL:**
- Verify VPC connector exists and is in same VPC as Cloud SQL
- Check Cloud SQL instance is in private IP mode
- Verify firewall rules allow traffic

**ModuleNotFoundError (Django import errors):**
- Check `DEBUG` is set
- Verify all environment variables are set
- Check `ALLOWED_HOSTS` includes Cloud Run domain

**Database authentication failed:**
- Verify DATABASE_URL is correct
- Check Cloud SQL credentials in Secret Manager
- Ensure database user has proper permissions

**Container won't start (exit code 137):**
- Increase memory limit (try 1Gi)
- Check logs for actual error
- Verify SECRET_KEY is set
