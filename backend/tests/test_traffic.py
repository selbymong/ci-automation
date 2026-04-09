import pytest


async def _setup(client):
    """Create user + charity. Return (token, charity_id)."""
    await client.post("/auth/register", json={
        "email": "traffic_admin@test.com", "password": "testpass123",
        "full_name": "Traffic Admin", "role": "admin",
    })
    login = await client.post("/auth/login", json={
        "email": "traffic_admin@test.com", "password": "testpass123",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    charity = await client.post("/charities/", json={
        "cra_number": "991991901RR0001", "formal_name": "Traffic Test Charity",
    }, headers=headers)
    charity_id = charity.json()["id"]

    return token, charity_id


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_snapshot(client):
    token, charity_id = await _setup(client)
    resp = await client.post("/traffic/", json={
        "charity_id": charity_id,
        "period_start": "2025-01-01",
        "period_end": "2025-01-31",
        "page_views": 1500,
        "active_users": 800,
        "avg_engagement_seconds": 45.5,
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["page_views"] == 1500
    assert data["active_users"] == 800


@pytest.mark.asyncio
async def test_batch_create(client):
    token, charity_id = await _setup(client)
    resp = await client.post("/traffic/batch", json=[
        {
            "charity_id": charity_id,
            "period_start": "2025-01-01", "period_end": "2025-01-31",
            "page_views": 1000, "active_users": 500,
        },
        {
            "charity_id": charity_id,
            "period_start": "2025-02-01", "period_end": "2025-02-28",
            "page_views": 1200, "active_users": 600,
        },
    ], headers=_auth(token))
    assert resp.status_code == 201
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_list_snapshots(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    await client.post("/traffic/", json={
        "charity_id": charity_id,
        "period_start": "2025-01-01", "period_end": "2025-01-31",
        "page_views": 500, "active_users": 200,
    }, headers=headers)

    resp = await client.get(f"/traffic/charity/{charity_id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_unauthenticated_rejected(client):
    resp = await client.post("/traffic/", json={
        "charity_id": "x",
        "period_start": "2025-01-01", "period_end": "2025-01-31",
        "page_views": 0, "active_users": 0,
    })
    assert resp.status_code in (401, 403)
