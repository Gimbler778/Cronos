from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from apps.api.routes import router

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(title="Cronos Timetable Optimizer", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/models")
def list_models() -> dict:
    """Expose the local model catalogue expected by OpenAI-compatible clients."""
    return {
        "object": "list",
        "data": [
            {
                "id": "cronos-optimizer",
                "object": "model",
                "created": 0,
                "owned_by": "cronos",
            }
        ],
    }
