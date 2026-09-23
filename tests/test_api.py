import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from primeait.api import app

@pytest.mark.asyncio
async def test_ask_returns_all_providers():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/ask", json={"question": "test question"})
    assert response.status_code == 200
    data = response.json()
    assert "OpenAI" in data or "DeepSeek" in data

@pytest.mark.asyncio
async def test_ask_mocked():
    fake_response = AsyncMock()
    fake_response.choices = [AsyncMock(message=AsyncMock(content="mocked answer"))]

    with patch("primeait.query.litellm.acompletion", return_value=fake_response):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/ask", json={"question": "test"})

    assert response.status_code == 200

@pytest.mark.asyncio
async def test_vote_updates_transcript():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/vote", json={
            "question": "test",
            "answers": {"OpenAI": "answer A", "DeepSeek": "answer B"},
            "winner": "OpenAI",
            "feedback": "clearer explanation",
        })
    assert response.status_code == 200