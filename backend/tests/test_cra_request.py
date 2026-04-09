import pytest


async def _setup(client):
    """Create user + charity. Return (token, charity_id)."""
    await client.post("/auth/register", json={
        "email": "cra_admin@test.com", "password": "testpass123",
        "full_name": "CRA Admin", "role": "admin",
    })
    login = await client.post("/auth/login", json={
        "email": "cra_admin@test.com", "password": "testpass123",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    charity = await client.post("/charities/", json={
        "cra_number": "700700701RR0001", "formal_name": "CRA Test Charity",
    }, headers=headers)
    charity_id = charity.json()["id"]

    return token, charity_id


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_cra_request(client):
    token, charity_id = await _setup(client)
    resp = await client.post("/cra-requests/", json={
        "charity_id": charity_id, "years_requested": "2022,2023",
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["charity_id"] == charity_id
    assert data["status"] == "pending"
    assert data["years_requested"] == "2022,2023"


@pytest.mark.asyncio
async def test_create_batch(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)

    # Create a second charity for batch
    c2 = await client.post("/charities/", json={
        "cra_number": "700700702RR0001", "formal_name": "CRA Batch Charity 2",
    }, headers=headers)
    charity_id_2 = c2.json()["id"]

    resp = await client.post("/cra-requests/batch", json={
        "charity_ids": [charity_id, charity_id_2],
        "years_requested": "2023",
        "batch_id": "BATCH-2025-01",
    }, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert len(data) == 2
    assert all(r["batch_id"] == "BATCH-2025-01" for r in data)


@pytest.mark.asyncio
async def test_list_requests(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    await client.post("/cra-requests/", json={
        "charity_id": charity_id, "years_requested": "2023",
    }, headers=headers)

    resp = await client.get("/cra-requests/", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_list_filter_by_status(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    await client.post("/cra-requests/", json={
        "charity_id": charity_id, "years_requested": "2023",
    }, headers=headers)

    resp = await client.get("/cra-requests/?status=pending", headers=headers)
    assert resp.status_code == 200
    assert all(r["status"] == "pending" for r in resp.json())


@pytest.mark.asyncio
async def test_list_filter_by_batch(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    await client.post("/cra-requests/", json={
        "charity_id": charity_id, "years_requested": "2023",
        "batch_id": "BATCH-FILTER-TEST",
    }, headers=headers)

    resp = await client.get(
        "/cra-requests/?batch_id=BATCH-FILTER-TEST", headers=headers
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_update_request(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/cra-requests/", json={
        "charity_id": charity_id, "years_requested": "2023",
    }, headers=headers)
    req_id = create.json()["id"]

    resp = await client.put(f"/cra-requests/{req_id}", json={
        "status": "received", "received_at": "2025-03-15",
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "received"
    assert data["received_at"] == "2025-03-15"


@pytest.mark.asyncio
async def test_update_not_found(client):
    token, _ = await _setup(client)
    resp = await client.put("/cra-requests/nonexistent", json={
        "status": "received",
    }, headers=_auth(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_rejected(client):
    resp = await client.get("/cra-requests/")
    assert resp.status_code in (401, 403)
