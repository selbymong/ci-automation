import pytest

from app.services.priority import (
    composite_to_rank,
    compute_composite,
    quintile_score,
    staleness_score,
)


# ── Unit tests for scoring functions ──

def test_quintile_score_top():
    values = [10, 20, 30, 40, 50]
    assert quintile_score(50, values) == 5.0


def test_quintile_score_bottom():
    values = [10, 20, 30, 40, 50]
    assert quintile_score(10, values) == 2.0  # 1/5 = 0.2 -> second quintile


def test_quintile_score_empty():
    assert quintile_score(10, []) == 1.0


def test_staleness_never_evaluated():
    assert staleness_score(None) == 5.0


def test_staleness_recent():
    assert staleness_score(0.5) == 1.0


def test_staleness_capped():
    assert staleness_score(10.0) == 5.0


def test_composite_calculation():
    result = compute_composite(5.0, 5.0, 5.0, 5.0)
    assert result == 5.0


def test_composite_to_rank_highest():
    assert composite_to_rank(4.5) == 1


def test_composite_to_rank_lowest():
    assert composite_to_rank(0.5) == 5


# ── Integration tests ──

async def _setup(client):
    await client.post("/auth/register", json={
        "email": "priority_user@test.com", "password": "testpass123",
        "full_name": "Priority User", "role": "analyst",
    })
    resp = await client.post("/auth/login", json={
        "email": "priority_user@test.com", "password": "testpass123",
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    charity = await client.post("/charities/", json={
        "cra_number": "333333333RR0001",
        "formal_name": "Priority Test Charity",
        "is_top_100": True,
    }, headers=headers)
    return token, charity.json()["id"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_calculate_priority(client):
    token, charity_id = await _setup(client)
    resp = await client.post(f"/priorities/{charity_id}/calculate", json={
        "page_views": 5000,
        "years_since_eval": 3.0,
        "demand_votes": 25,
    }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["charity_id"] == charity_id
    assert data["top100_bonus"] == 5.0
    assert data["priority_rank"] >= 1
    assert data["priority_rank"] <= 5


@pytest.mark.asyncio
async def test_calculate_priority_not_found(client):
    await client.post("/auth/register", json={
        "email": "pnf@test.com", "password": "testpass123",
        "full_name": "Test", "role": "analyst",
    })
    login = await client.post("/auth/login", json={
        "email": "pnf@test.com", "password": "testpass123",
    })
    token = login.json()["access_token"]
    resp = await client.post("/priorities/nonexistent/calculate", json={
        "page_views": 100,
    }, headers=_auth(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_priority(client):
    token, charity_id = await _setup(client)
    await client.post(f"/priorities/{charity_id}/calculate", json={
        "page_views": 1000,
    }, headers=_auth(token))
    resp = await client.get(f"/priorities/{charity_id}", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["charity_id"] == charity_id


@pytest.mark.asyncio
async def test_priority_queue(client):
    token, charity_id = await _setup(client)
    await client.post(f"/priorities/{charity_id}/calculate", json={
        "page_views": 1000,
        "years_since_eval": 2.0,
    }, headers=_auth(token))
    resp = await client.get("/priorities/", headers=_auth(token))
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    assert items[0]["charity_id"] == charity_id


@pytest.mark.asyncio
async def test_recalculate_updates_existing(client):
    token, charity_id = await _setup(client)
    await client.post(f"/priorities/{charity_id}/calculate", json={
        "page_views": 100,
    }, headers=_auth(token))
    resp = await client.post(f"/priorities/{charity_id}/calculate", json={
        "page_views": 9999,
        "years_since_eval": 5.0,
    }, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["page_views"] == 9999
