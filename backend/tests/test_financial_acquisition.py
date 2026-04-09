import pytest


async def _setup(client):
    """Create user, charity, cycle. Return (token, charity_id, cycle_id)."""
    await client.post("/auth/register", json={
        "email": "fa_admin@test.com", "password": "testpass123",
        "full_name": "FA Admin", "role": "admin",
    })
    login = await client.post("/auth/login", json={
        "email": "fa_admin@test.com", "password": "testpass123",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    charity = await client.post("/charities/", json={
        "cra_number": "600600601RR0001", "formal_name": "FA Test Charity",
    }, headers=headers)
    charity_id = charity.json()["id"]

    cycle = await client.post("/cycles/", json={"name": "FA Cycle"}, headers=headers)
    cycle_id = cycle.json()["id"]

    return token, charity_id, cycle_id


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_acquisition(client):
    token, charity_id, cycle_id = await _setup(client)
    resp = await client.post("/financial-acquisitions/", json={
        "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["charity_id"] == charity_id
    assert data["cycle_id"] == cycle_id
    assert data["status"] == "not_started"


@pytest.mark.asyncio
async def test_duplicate_acquisition_rejected(client):
    token, charity_id, cycle_id = await _setup(client)
    headers = _auth(token)
    await client.post("/financial-acquisitions/", json={
        "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=headers)
    resp = await client.post("/financial-acquisitions/", json={
        "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_acquisition(client):
    token, charity_id, cycle_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/financial-acquisitions/", json={
        "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=headers)
    acq_id = create.json()["id"]

    resp = await client.get(f"/financial-acquisitions/{acq_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == acq_id


@pytest.mark.asyncio
async def test_get_acquisition_not_found(client):
    token, _, _ = await _setup(client)
    resp = await client.get(
        "/financial-acquisitions/nonexistent-id", headers=_auth(token)
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_acquisition(client):
    token, charity_id, cycle_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/financial-acquisitions/", json={
        "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=headers)
    acq_id = create.json()["id"]

    resp = await client.put(f"/financial-acquisitions/{acq_id}", json={
        "status": "afs_checked",
        "afs_url": "https://example.com/afs.pdf",
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "afs_checked"
    assert data["afs_url"] == "https://example.com/afs.pdf"


@pytest.mark.asyncio
async def test_list_by_cycle(client):
    token, charity_id, cycle_id = await _setup(client)
    headers = _auth(token)
    await client.post("/financial-acquisitions/", json={
        "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=headers)

    resp = await client.get(
        f"/financial-acquisitions/cycle/{cycle_id}", headers=headers
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_escalation_flag_not_set_initially(client):
    token, charity_id, cycle_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/financial-acquisitions/", json={
        "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=headers)
    data = create.json()
    assert data["escalation_needed"] is None


@pytest.mark.asyncio
async def test_unauthenticated_rejected(client):
    resp = await client.post("/financial-acquisitions/", json={
        "charity_id": "x", "cycle_id": "y",
    })
    assert resp.status_code in (401, 403)
