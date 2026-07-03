# Start Here

This is a clean FastAPI boilerplate for the SHL conversational assessment recommender task.

The goal is simple:

```text
User message history
    -> FastAPI /chat
    -> understand role + constraints
    -> recommend only SHL catalog items
    -> return the exact evaluator JSON schema
```

No frontend is required for submission. The evaluator only needs your public API URL.

## 1. What Is Inside

```text
app/
  main.py          API entry point. Contains /health and /chat.
  schemas.py       Request and response models. Do not casually change this.
  catalog.py       Loads app/data/catalog.json and formats recommendations.
  retriever.py     Simple keyword search over the SHL catalog.
  policy.py        Main conversation logic: clarify, recommend, refine, compare, refuse.
  data/catalog.json
                   Bundled SHL catalog data.

tests/
  test_api.py      Basic tests for health, vague query, and schema-valid recommendations.

scripts/
  smoke_test.py    Quick script to test a running local server.

Dockerfile         Used by Google Cloud Run or any Docker host.
requirements.txt  Python dependencies.
```

## 2. Run Locally On Windows

Open terminal inside this folder.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open this in your browser:

```text
http://127.0.0.1:8000/docs
```

Check health:

```text
http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"ok"}
```

## 3. Test The Chat Endpoint

In the FastAPI docs, open `POST /chat` and try:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "I am hiring a senior Java engineer with Spring, SQL, AWS and Docker."
    }
  ]
}
```

You should get:

```json
{
  "reply": "...",
  "recommendations": [
    {
      "name": "...",
      "url": "...",
      "test_type": "..."
    }
  ],
  "end_of_conversation": false
}
```

## 4. Run Tests

```powershell
pytest
```

## 5. Where You Should Edit

Most of your work will be in two files:

```text
app/policy.py
app/retriever.py
```

Use `app/policy.py` when you want to improve conversation behavior.

Examples:

- ask a better clarification question
- add a known shortlist for a public sample conversation
- handle "drop OPQ"
- handle "add personality"
- handle comparison questions
- refuse legal or off-topic questions

Use `app/retriever.py` when you want better general search.

The current search is intentionally simple and fast. You can later upgrade it to BM25, FAISS, Chroma, or embeddings.

## 6. Deployment Recommendation

Use Google Cloud Run.

Why:

- It runs normal FastAPI Docker apps.
- It gives a public HTTPS URL.
- It is easier than Cloudflare Workers for Python/FastAPI.
- The evaluator can call `/health` and `/chat` directly.

## 7. Deploy To Google Cloud Run

Install first:

- Git
- Docker Desktop
- Google Cloud CLI

Then run:

```powershell
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
gcloud run deploy shl-agent --source . --region asia-south1 --allow-unauthenticated
```

When deployment finishes, Google prints a URL like:

```text
https://shl-agent-xxxxx-uc.a.run.app
```

Test:

```powershell
curl https://YOUR_SERVICE_URL/health
```

Submit this base URL:

```text
https://YOUR_SERVICE_URL
```

The evaluator will call:

```text
GET /health
POST /chat
```

## 8. Important Evaluator Rules

Keep these sacred:

- Always return `reply`, `recommendations`, and `end_of_conversation`.
- `recommendations` must be an empty array when clarifying or refusing.
- When recommending, return 1 to 10 items.
- Every recommendation URL must come from `catalog.json`.
- Do not store chat state on the server.
- Use the full message history sent in the request.
- Keep responses fast, under 30 seconds.

## 9. Common Fix

If the app crashes on catalog loading, make sure `app/catalog.py` uses:

```python
raw = json.loads(f.read(), strict=False)
```

This project already has that fix.

