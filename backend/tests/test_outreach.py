import pytest


async def _setup(client):
    """Create admin, charity, cycle, evaluation. Return (token, eval_id, charity_id)."""
    await client.post("/auth/register", json={
        "email": "outreach_admin@test.com", "password": "testpass123",
        "full_name": "Outreach Admin", "role": "admin",
    })
    login = await client.post("/auth/login", json={
        "email": "outreach_admin@test.com", "password": "testpass123",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    charity = await client.post("/charities/", json={
        "cra_number": "970970901RR0001", "formal_name": "Outreach Test Charity",
    }, headers=headers)
    charity_id = charity.json()["id"]

    cycle = await client.post("/cycles/", json={"name": "Outreach Cycle"}, headers=headers)
    eval_resp = await client.post("/evaluations/", json={
        "charity_id": charity_id, "cycle_id": cycle.json()["id"],
    }, headers=headers)
    eval_id = eval_resp.json()["id"]

    return token, eval_id, charity_id


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_outreach(client):
    token, eval_id, charity_id = await _setup(client)
    resp = await client.post("/outreach/", json={
        "evaluation_id": eval_id, "charity_id": charity_id,
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["evaluation_id"] == eval_id
    assert data["charity_id"] == charity_id
    assert data["response_received"] is False


@pytest.mark.asyncio
async def test_get_outreach(client):
    token, eval_id, charity_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/outreach/", json={
        "evaluation_id": eval_id, "charity_id": charity_id,
    }, headers=headers)
    outreach_id = create.json()["id"]

    resp = await client.get(f"/outreach/{outreach_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == outreach_id


@pytest.mark.asyncio
async def test_update_outreach_send_profile(client):
    token, eval_id, charity_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/outreach/", json={
        "evaluation_id": eval_id, "charity_id": charity_id,
    }, headers=headers)
    outreach_id = create.json()["id"]

    resp = await client.put(f"/outreach/{outreach_id}", json={
        "profile_sent_at": "2025-03-15",
        "sent_to_email": "charity@example.com",
        "email_saved": True,
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["profile_sent_at"] == "2025-03-15"
    assert data["sent_to_email"] == "charity@example.com"
    assert data["email_saved"] is True


@pytest.mark.asyncio
async def test_update_outreach_record_response(client):
    token, eval_id, charity_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/outreach/", json={
        "evaluation_id": eval_id, "charity_id": charity_id,
    }, headers=headers)
    outreach_id = create.json()["id"]

    resp = await client.put(f"/outreach/{outreach_id}", json={
        "response_received": True,
        "response_received_at": "2025-04-01",
        "charity_adds_content": "We would like to add that...",
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["response_received"] is True
    assert data["charity_adds_content"] == "We would like to add that..."


@pytest.mark.asyncio
async def test_list_by_evaluation(client):
    token, eval_id, charity_id = await _setup(client)
    headers = _auth(token)
    await client.post("/outreach/", json={
        "evaluation_id": eval_id, "charity_id": charity_id,
    }, headers=headers)

    resp = await client.get(f"/outreach/evaluation/{eval_id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_get_not_found(client):
    token, _, _ = await _setup(client)
    resp = await client.get("/outreach/nonexistent", headers=_auth(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_rejected(client):
    resp = await client.post("/outreach/", json={
        "evaluation_id": "x", "charity_id": "y",
    })
    assert resp.status_code in (401, 403)
