import pytest


async def _setup(client):
    """Create admin, analyst, charity, cycle. Return (admin_token, analyst_id, charity_id, cycle_id)."""
    await client.post("/auth/register", json={
        "email": "assign_admin@test.com", "password": "testpass123",
        "full_name": "Assign Admin", "role": "admin",
    })
    admin_login = await client.post("/auth/login", json={
        "email": "assign_admin@test.com", "password": "testpass123",
    })
    admin_token = admin_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    await client.post("/auth/register", json={
        "email": "assign_analyst@test.com", "password": "testpass123",
        "full_name": "Assign Analyst", "role": "analyst",
    })
    analyst_login = await client.post("/auth/login", json={
        "email": "assign_analyst@test.com", "password": "testpass123",
    })
    analyst_me = await client.get("/auth/me", headers={
        "Authorization": f"Bearer {analyst_login.json()['access_token']}"
    })
    analyst_id = analyst_me.json()["id"]

    charity = await client.post("/charities/", json={
        "cra_number": "444444444RR0001", "formal_name": "Assignment Charity",
    }, headers=headers)
    charity_id = charity.json()["id"]

    cycle = await client.post("/cycles/", json={"name": "Assign Cycle"}, headers=headers)
    cycle_id = cycle.json()["id"]

    return admin_token, analyst_id, charity_id, cycle_id


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_assignment(client):
    admin_token, analyst_id, charity_id, cycle_id = await _setup(client)
    resp = await client.post("/assignments/", json={
        "analyst_id": analyst_id,
        "charity_id": charity_id,
        "cycle_id": cycle_id,
    }, headers=_auth(admin_token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["analyst_id"] == analyst_id
    assert data["charity_id"] == charity_id


@pytest.mark.asyncio
async def test_duplicate_assignment(client):
    admin_token, analyst_id, charity_id, cycle_id = await _setup(client)
    await client.post("/assignments/", json={
        "analyst_id": analyst_id, "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=_auth(admin_token))
    resp = await client.post("/assignments/", json={
        "analyst_id": analyst_id, "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=_auth(admin_token))
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_bulk_assign(client):
    admin_token, analyst_id, _, cycle_id = await _setup(client)
    headers = _auth(admin_token)
    c1 = await client.post("/charities/", json={
        "cra_number": "555555551RR0001", "formal_name": "Bulk 1",
    }, headers=headers)
    c2 = await client.post("/charities/", json={
        "cra_number": "555555552RR0001", "formal_name": "Bulk 2",
    }, headers=headers)
    resp = await client.post("/assignments/bulk", json={
        "analyst_id": analyst_id,
        "charity_ids": [c1.json()["id"], c2.json()["id"]],
        "cycle_id": cycle_id,
    }, headers=headers)
    assert resp.status_code == 201
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_list_assignments_by_cycle(client):
    admin_token, analyst_id, charity_id, cycle_id = await _setup(client)
    headers = _auth(admin_token)
    await client.post("/assignments/", json={
        "analyst_id": analyst_id, "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=headers)
    resp = await client.get(f"/assignments/cycle/{cycle_id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_reassign(client):
    admin_token, analyst_id, charity_id, cycle_id = await _setup(client)
    headers = _auth(admin_token)

    # Create second analyst
    await client.post("/auth/register", json={
        "email": "analyst2@test.com", "password": "testpass123",
        "full_name": "Analyst Two", "role": "analyst",
    })
    a2_login = await client.post("/auth/login", json={
        "email": "analyst2@test.com", "password": "testpass123",
    })
    a2_me = await client.get("/auth/me", headers={
        "Authorization": f"Bearer {a2_login.json()['access_token']}"
    })
    analyst2_id = a2_me.json()["id"]

    create = await client.post("/assignments/", json={
        "analyst_id": analyst_id, "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=headers)
    assignment_id = create.json()["id"]

    resp = await client.post(f"/assignments/{assignment_id}/reassign", json={
        "new_analyst_id": analyst2_id,
        "reason": "Workload rebalancing",
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["analyst_id"] == analyst2_id
    assert data["reassigned_from_id"] == analyst_id
    assert data["reassignment_reason"] == "Workload rebalancing"


@pytest.mark.asyncio
async def test_workload_balance(client):
    admin_token, analyst_id, charity_id, cycle_id = await _setup(client)
    headers = _auth(admin_token)
    await client.post("/assignments/", json={
        "analyst_id": analyst_id, "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=headers)
    resp = await client.get(f"/assignments/workload/{cycle_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["analyst_id"] == analyst_id
    assert data[0]["assignment_count"] == 1


@pytest.mark.asyncio
async def test_analyst_cannot_assign(client):
    _, analyst_id, charity_id, cycle_id = await _setup(client)
    # Login as analyst
    login = await client.post("/auth/login", json={
        "email": "assign_analyst@test.com", "password": "testpass123",
    })
    analyst_token = login.json()["access_token"]
    resp = await client.post("/assignments/", json={
        "analyst_id": analyst_id, "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=_auth(analyst_token))
    assert resp.status_code == 403
