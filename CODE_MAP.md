# Code Map

## Request Flow

```text
POST /chat
    -> app/main.py
    -> app/schemas.py
    -> app/policy.py
    -> app/retriever.py
    -> app/catalog.py
    -> JSON response
```

## File Purpose

```text
app/main.py
  Creates FastAPI app.
  Defines /health and /chat.

app/schemas.py
  Defines input and output schema.
  Keep this aligned with the evaluator.

app/catalog.py
  Loads catalog.json.
  Converts catalog items to {name, url, test_type}.
  Keeps recommendations catalog-grounded.

app/retriever.py
  Fallback keyword search.
  Improve this if recommendations are weak.

app/policy.py
  Conversation decision logic.
  This is the main file to tune.

tests/test_api.py
  Basic tests.
```

## Best Development Loop

```text
1. Run uvicorn.
2. Try a sample conversation in /docs.
3. Tune app/policy.py.
4. Run pytest.
5. Repeat.
```

