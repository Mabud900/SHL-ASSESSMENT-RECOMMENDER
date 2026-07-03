# Deploy Guide

## Recommended: Google Cloud Run

Google Cloud Run is the cleanest deployment option for this task.

From the project folder:

```powershell
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
gcloud run deploy shl-agent --source . --region asia-south1 --allow-unauthenticated
```

Then test:

```powershell
curl https://YOUR_SERVICE_URL/health
```

Expected:

```json
{"status":"ok"}
```

## Docker Local Test

```powershell
docker build -t shl-agent .
docker run -p 8080:8080 shl-agent
```

Open:

```text
http://127.0.0.1:8080/health
```

## Cloudflare

Use Cloudflare only if:

- you are using Cloudflare Containers, or
- you are using Cloudflare as DNS/proxy in front of Cloud Run.

For this Python FastAPI service, Cloud Run is simpler.

## ByteXL

Use ByteXL only if it supports:

- installing Python packages,
- running a long-lived FastAPI server,
- exposing a public HTTPS URL,
- accepting POST requests from the evaluator.

If not, use ByteXL only for practice, not final submission.

