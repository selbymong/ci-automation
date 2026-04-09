import pytest


async def _admin_token(client):
    await client.post("/auth/register", json={
        "email": "cycle_admin@test.com", "password": "testpass123",
        "full_name": "Cycle Admin", "role": "admin",
    })
    resp = await client.post("/auth/login", json={
        "email": "cycle_admin@test.com", "password": "testpass123",
    })
    return resp.json()["access_token"]


async def _analyst_token(client):
    await client.post("/auth/register", json={
        "email": "cycle_analyst@test.com", "password": "testpass123",
        "full_name": "Cycle Analyst", "role": "analyst",
    })
    resp = await client.post("/auth/login", json={
        "email": "cycle_analyst@test.com", "password": "testpass123",
    })
    return resp.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_cycle(client):
    token = await _admin_token(client)
    resp = await client.post("/cycles/", json={
        "name": "Summer 2025",
        "start_date": "2025-05-01",
        "end_date": "2025-08-31",
        "target_count": 150,
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Summer 2025"
    assert data["status"] == "planning"
    assert data["target_count"] == 150


@pytest.mark.asyncio
async def test_create_cycle_non_admin(client):
    token = await _analyst_token(client)
    resp = await client.post("/cycles/", json={
        "name": "Unauthorized Cycle",
    }, headers=_auth(token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_cycle_duplicate(client):
    token = await _admin_token(client)
    await client.post("/cycles/", json={"name": "Dup Cycle"}, headers=_auth(token))
    resp = await client.post("/cycles/", json={"name": "Dup Cycle"}, headers=_auth(token))
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_cycles(client):
    token = await _admin_token(client)
    await client.post("/cycles/", json={"name": "Cycle A"}, headers=_auth(token))
    await client.post("/cycles/", json={"name": "Cycle B"}, headers=_auth(token))
    # Analysts can list
    analyst = await _analyst_token(client)
    resp = await client.get("/cycles/", headers=_auth(analyst))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_cycle(client):
    token = await _admin_token(client)
    create = await client.post("/cycles/", json={"name": "Get Test"}, headers=_auth(token))
    cycle_id = create.json()["id"]
    resp = await client.get(f"/cycles/{cycle_id}", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get Test"


@pytest.mark.asyncio
async def test_update_cycle(client):
    token = await _admin_token(client)
    create = await client.post("/cycles/", json={
        "name": "Update Me", "target_count": 100,
    }, headers=_auth(token))
    cycle_id = create.json()["id"]
    resp = await client.put(f"/cycles/{cycle_id}", json={
        "target_count": 200,
    }, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["target_count"] == 200
    assert resp.json()["name"] == "Update Me"


@pytest.mark.asyncio
async def test_transition_planning_to_active(client):
    token = await _admin_token(client)
    create = await client.post("/cycles/", json={"name": "Trans Cycle"}, headers=_auth(token))
    cycle_id = create.json()["id"]
    resp = await client.post(f"/cycles/{cycle_id}/transition", json={
        "status": "active",
    }, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


@pytest.mark.asyncio
async def test_transition_active_to_review(client):
    token = await _admin_token(client)
    create = await client.post("/cycles/", json={"name": "Full Trans"}, headers=_auth(token))
    cycle_id = create.json()["id"]
    await client.post(f"/cycles/{cycle_id}/transition", json={"status": "active"}, headers=_auth(token))
    resp = await client.post(f"/cycles/{cycle_id}/transition", json={"status": "review"}, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "review"


@pytest.mark.asyncio
async def test_transition_review_to_closed(client):
    token = await _admin_token(client)
    create = await client.post("/cycles/", json={"name": "Close Cycle"}, headers=_auth(token))
    cycle_id = create.json()["id"]
    await client.post(f"/cycles/{cycle_id}/transition", json={"status": "active"}, headers=_auth(token))
    await client.post(f"/cycles/{cycle_id}/transition", json={"status": "review"}, headers=_auth(token))
    resp = await client.post(f"/cycles/{cycle_id}/transition", json={"status": "closed"}, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"


@pytest.mark.asyncio
async def test_invalid_transition(client):
    token = await _admin_token(client)
    create = await client.post("/cycles/", json={"name": "Bad Trans"}, headers=_auth(token))
    cycle_id = create.json()["id"]
    # planning -> closed is not allowed
    resp = await client.post(f"/cycles/{cycle_id}/transition", json={"status": "closed"}, headers=_auth(token))
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_closed_cycle_no_transitions(client):
    token = await _admin_token(client)
    create = await client.post("/cycles/", json={"name": "Locked Cycle"}, headers=_auth(token))
    cycle_id = create.json()["id"]
    await client.post(f"/cycles/{cycle_id}/transition", json={"status": "active"}, headers=_auth(token))
    await client.post(f"/cycles/{cycle_id}/transition", json={"status": "review"}, headers=_auth(token))
    await client.post(f"/cycles/{cycle_id}/transition", json={"status": "closed"}, headers=_auth(token))
    resp = await client.post(f"/cycles/{cycle_id}/transition", json={"status": "active"}, headers=_auth(token))
    assert resp.status_code == 400
