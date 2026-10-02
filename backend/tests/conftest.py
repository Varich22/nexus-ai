"""Pytest fixtures."""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Ensure tests don't hit real APIs
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-used")
os.environ.setdefault("ENVIRONMENT", "test")


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    from app.main import app

    with TestClient(app) as c:
        yield c
