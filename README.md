# SHL Assessment Agent Boilerplate

Clean code boilerplate for the SHL GenAI conversational assessment-selection task.

Start with:

```text
START_HERE.md
```

The app is a stateless FastAPI API:

```text
GET  /health
POST /chat
```

It uses the bundled SHL catalog at:

```text
app/data/catalog.json
```

Main files:

```text
app/main.py       FastAPI routes
app/schemas.py    JSON schema
app/catalog.py    catalog loading
app/retriever.py  search
app/policy.py     conversation logic
```

Run locally:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

