from pathlib import Path
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from apps.api.routes import router
from apps.api.storage import StorageError

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(title="Cronos Timetable Optimizer", version="0.1.0")
allowed_origins = [
    origin.strip()
    for origin in os.getenv("CRONOS_WEB_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api/v1")


@app.exception_handler(StorageError)
def storage_error_handler(_request, error: StorageError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": {"code": "STORAGE_UNAVAILABLE", "message": str(error)}},
    )


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
