"""Vercel serverless entrypoint for the Cronos FastAPI application."""

from apps.api.main import app

__all__ = ["app"]
