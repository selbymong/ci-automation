import pytest


async def _setup(client):
    """Create admin user + charity. Return (token, charity_id, charity_name)."""
    await client.post("/auth/register", json={
        "email": "demand_admin@test.com", "password": "testpass123",
        "full_name": "Demand Admin", "role": "admin",
    })
    login = await client.post("/auth/login", json={
        "email": "demand_admin@test.com", "password": "testpass123",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    charity = await client.post("/charities/", json={
        "cra_number": "980980901RR0001",
        "formal_name": "Demand Test Foundation",
        "common_name": "Demand Test",
    }, headers=headers)
    charity_id = charity.json()["id"]

    return token, charity_id, "Demand Test Foundation"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_request_matched(client):
    """Public request matches an existing charity."""
    token, charity_id, charity_name = await _setup(client)
    # Public endpoint - no auth needed
    resp = await client.post("/demand/requests", json={
        "requester_name": "John Doe",
        "requester_email": "john@example.com",
        "requested_charity_name": "Demand Test Foundation",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "matched"
    assert data["matched_charity_id"] == charity_id


@pytest.mark.asyncio
async def test_create_request_unmatched(client):
    """Public request with no matching charity."""
    await _setup(client)
    resp = await client.post("/demand/requests", json={
        "requester_name": "Jane Doe",
        "requester_email": "jane@example.com",
        "requested_charity_name": "Nonexistent Charity XYZ",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "unmatched"
    assert data["matched_charity_id"] is None


@pytest.mark.asyncio
async def test_fuzzy_match_partial_name(client):
    """Fuzzy match works with partial name."""
    token, charity_id, _ = await _setup(client)
    resp = await client.post("/demand/requests", json={
        "requester_name": "User",
        "requester_email": "user@example.com",
        "requested_charity_name": "demand test",  # lowercase partial
    })
    assert resp.status_code == 201
    assert resp.json()["status"] == "matched"


@pytest.mark.asyncio
async def test_aggregate_increments_on_match(client):
    token, charity_id, _ = await _setup(client)
    headers = _auth(token)

    # Two matched requests
    await client.post("/demand/requests", json={
        "requester_name": "User 1", "requester_email": "u1@example.com",
        "requested_charity_name": "Demand Test Foundation",
    })
    await client.post("/demand/requests", json={
        "requester_name": "User 2", "requester_email": "u2@example.com",
        "requested_charity_name": "Demand Test Foundation",
    })

    resp = await client.get("/demand/aggregates", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    agg = [a for a in data if a["charity_id"] == charity_id][0]
    assert agg["vote_count"] == 2


@pytest.mark.asyncio
async def test_list_requests(client):
    token, _, _ = await _setup(client)
    await client.post("/demand/requests", json={
        "requester_name": "X", "requester_email": "x@example.com",
        "requested_charity_name": "Demand Test Foundation",
    })

    resp = await client.get("/demand/requests", headers=_auth(token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_list_requests_filter_by_status(client):
    token, _, _ = await _setup(client)
    await client.post("/demand/requests", json={
        "requester_name": "Y", "requester_email": "y@example.com",
        "requested_charity_name": "No Match Here",
    })

    resp = await client.get("/demand/requests?status=unmatched", headers=_auth(token))
    assert resp.status_code == 200
    assert all(r["status"] == "unmatched" for r in resp.json())


@pytest.mark.asyncio
async def test_update_request_disposition(client):
    token, _, _ = await _setup(client)
    create = await client.post("/demand/requests", json={
        "requester_name": "Z", "requester_email": "z@example.com",
        "requested_charity_name": "No Match",
    })
    req_id = create.json()["id"]

    resp = await client.put(f"/demand/requests/{req_id}", json={
        "disposition": "not_a_charity",
    }, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["disposition"] == "not_a_charity"


@pytest.mark.asyncio
async def test_update_request_invalid_disposition(client):
    token, _, _ = await _setup(client)
    create = await client.post("/demand/requests", json={
        "requester_name": "W", "requester_email": "w@example.com",
        "requested_charity_name": "No Match",
    })
    req_id = create.json()["id"]

    resp = await client.put(f"/demand/requests/{req_id}", json={
        "disposition": "invalid_type",
    }, headers=_auth(token))
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_aggregate_disposition(client):
    token, charity_id, _ = await _setup(client)
    headers = _auth(token)
    # Create a matched request to generate aggregate
    await client.post("/demand/requests", json={
        "requester_name": "V", "requester_email": "v@example.com",
        "requested_charity_name": "Demand Test Foundation",
    })

    aggs = await client.get("/demand/aggregates", headers=headers)
    agg_id = [a for a in aggs.json() if a["charity_id"] == charity_id][0]["id"]

    resp = await client.put(f"/demand/aggregates/{agg_id}", json={
        "disposition": "done",
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["disposition"] == "done"


@pytest.mark.asyncio
async def test_list_requests_requires_auth(client):
    resp = await client.get("/demand/requests")
    assert resp.status_code in (401, 403)
