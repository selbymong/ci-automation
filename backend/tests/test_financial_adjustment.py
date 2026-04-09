import pytest


async def _setup(client):
    """Create user + charity. Return (token, charity_id)."""
    await client.post("/auth/register", json={
        "email": "adj_admin@test.com", "password": "testpass123",
        "full_name": "Adj Admin", "role": "admin",
    })
    login = await client.post("/auth/login", json={
        "email": "adj_admin@test.com", "password": "testpass123",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    charity = await client.post("/charities/", json={
        "cra_number": "920920901RR0001", "formal_name": "Adjustment Test Charity",
    }, headers=headers)
    charity_id = charity.json()["id"]

    return token, charity_id


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_adjustment(client):
    token, charity_id = await _setup(client)
    resp = await client.post("/financial-adjustments/", json={
        "charity_id": charity_id,
        "adjustment_type": "deferred_contributions",
        "description": "Removed deferred revenue of $50k",
        "amount": -50000.0,
        "field_affected": "total_revenue",
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["adjustment_type"] == "deferred_contributions"
    assert data["amount"] == -50000.0


@pytest.mark.asyncio
async def test_create_adjustment_invalid_type(client):
    token, charity_id = await _setup(client)
    resp = await client.post("/financial-adjustments/", json={
        "charity_id": charity_id,
        "adjustment_type": "invalid_type",
        "description": "Bad type",
    }, headers=_auth(token))
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_adjustments(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    await client.post("/financial-adjustments/", json={
        "charity_id": charity_id,
        "adjustment_type": "amortization",
        "description": "Amortization adjustment",
    }, headers=headers)
    await client.post("/financial-adjustments/", json={
        "charity_id": charity_id,
        "adjustment_type": "reclassification",
        "description": "Reclassify admin to program",
    }, headers=headers)

    resp = await client.get(f"/financial-adjustments/charity/{charity_id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_update_adjustment(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/financial-adjustments/", json={
        "charity_id": charity_id,
        "adjustment_type": "other",
        "description": "Original",
    }, headers=headers)
    adj_id = create.json()["id"]

    resp = await client.put(f"/financial-adjustments/{adj_id}", json={
        "description": "Updated description",
        "amount": 25000.0,
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["description"] == "Updated description"
    assert resp.json()["amount"] == 25000.0


@pytest.mark.asyncio
async def test_delete_adjustment(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/financial-adjustments/", json={
        "charity_id": charity_id,
        "adjustment_type": "consolidation",
        "description": "To delete",
    }, headers=headers)
    adj_id = create.json()["id"]

    resp = await client.delete(f"/financial-adjustments/{adj_id}", headers=headers)
    assert resp.status_code == 204

    # Verify gone
    resp = await client.get(f"/financial-adjustments/charity/{charity_id}", headers=headers)
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_update_not_found(client):
    token, _ = await _setup(client)
    resp = await client.put("/financial-adjustments/nonexistent", json={
        "description": "X",
    }, headers=_auth(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_rejected(client):
    resp = await client.post("/financial-adjustments/", json={
        "charity_id": "x", "adjustment_type": "other", "description": "nope",
    })
    assert resp.status_code in (401, 403)
