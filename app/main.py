from fastapi import FastAPI

from app.catalog import load_catalog
from app.policy import answer
from app.schemas import ChatRequest, ChatResponse


app = FastAPI(title="SHL Conversational Assessment Recommender")


@app.on_event("startup")
def warm_catalog() -> None:
    load_catalog()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return answer(request.messages)

