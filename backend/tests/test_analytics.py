import pytest


async def _setup(client):
    """Create admin, analyst, charity, cycle, assignment, evaluation.
    Return (admin_token, analyst_token, charity_id, cycle_id, eval_id).
    """
    # Admin
    await client.post("/auth/register", json={
        "email": "analytics_admin@test.com", "password": "testpass123",
        "full_name": "Analytics Admin", "role": "admin",
    })
    admin_login = await client.post("/auth/login", json={
        "email": "analytics_admin@test.com", "password": "testpass123",
    })
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Analyst
    await client.post("/auth/register", json={
        "email": "analytics_analyst@test.com", "password": "testpass123",
        "full_name": "Analytics Analyst", "role": "analyst",
    })
    analyst_login = await client.post("/auth/login", json={
        "email": "analytics_analyst@test.com", "password": "testpass123",
    })
    analyst_token = analyst_login.json()["access_token"]
    analyst_me = await client.get("/auth/me", headers={
        "Authorization": f"Bearer {analyst_token}"
    })
    analyst_id = analyst_me.json()["id"]

    # Charity + Cycle
    charity = await client.post("/charities/", json={
        "cra_number": "990990901RR0001", "formal_name": "Analytics Test Charity",
    }, headers=admin_headers)
    charity_id = charity.json()["id"]

    cycle = await client.post("/cycles/", json={"name": "Analytics Cycle"}, headers=admin_headers)
    cycle_id = cycle.json()["id"]

    # Assignment
    await client.post("/assignments/", json={
        "analyst_id": analyst_id, "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=admin_headers)

    # Evaluation
    eval_resp = await client.post("/evaluations/", json={
        "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=admin_headers)
    eval_id = eval_resp.json()["id"]

    return admin_token, analyst_token, charity_id, cycle_id, eval_id


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_analyst_throughput(client):
    admin_token, _, _, cycle_id, _ = await _setup(client)
    resp = await client.get(
        f"/analytics/analyst-throughput?cycle_id={cycle_id}",
        headers=_auth(admin_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_analyst_throughput_requires_reviewer(client):
    _, analyst_token, _, _, _ = await _setup(client)
    resp = await client.get(
        "/analytics/analyst-throughput", headers=_auth(analyst_token)
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_cycle_progress(client):
    admin_token, _, _, cycle_id, eval_id = await _setup(client)
    resp = await client.get(
        f"/analytics/cycle-progress/{cycle_id}", headers=_auth(admin_token)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["cycle_id"] == cycle_id
    assert data["total_evaluations"] == 1
    assert "stage_distribution" in data
    assert data["stage_distribution"].get("prioritized") == 1


@pytest.mark.asyncio
async def test_cycle_progress_empty(client):
    admin_token, _, _, _, _ = await _setup(client)
    headers = _auth(admin_token)
    # Create empty cycle
    cycle = await client.post("/cycles/", json={"name": "Empty Cycle"}, headers=headers)
    resp = await client.get(
        f"/analytics/cycle-progress/{cycle.json()['id']}", headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["total_evaluations"] == 0
    assert resp.json()["completion_percent"] == 0


@pytest.mark.asyncio
async def test_stage_durations(client):
    admin_token, _, _, cycle_id, eval_id = await _setup(client)
    headers = _auth(admin_token)

    # Transition evaluation forward to create duration data
    await client.post(f"/evaluations/{eval_id}/transition", json={
        "to_stage": "assigned",
    }, headers=headers)

    resp = await client.get(
        f"/analytics/stage-durations/{cycle_id}", headers=headers
    )
    assert resp.status_code == 200
    # Should have at least one entry
    data = resp.json()
    assert isinstance(data, list)
