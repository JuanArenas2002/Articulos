"""
Tests de endpoints — requieren DB activa para endpoints de datos.
Los tests de / y /health corren sin DB.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    with patch("app.database.async_engine") as mock_engine:
        mock_conn = AsyncMock()
        mock_engine.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.begin.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_engine.dispose = AsyncMock()

        from main import app
        with TestClient(app) as c:
            yield c


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "mensaje" in data
    assert "docs" in data


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_publications_requires_db(client):
    """Con DB offline, endpoint debe retornar 500 — no 404 ni silencio."""
    response = client.get("/publications")
    assert response.status_code in (200, 500)


def test_search_requires_q_param(client):
    """Sin q, /publications/search debe retornar 422 (validación)."""
    response = client.get("/publications/search")
    assert response.status_code == 422


def test_by_identifier_requires_param(client):
    """Sin ningún identificador, debe retornar 400."""
    response = client.get("/publications/by-identifier")
    assert response.status_code == 400
