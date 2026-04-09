"""Tests for F072: Data export API for Harness consumption."""

import pytest

API_KEY = "evaluator-export-key-dev"


async def _setup(client):
    """Create admin, charity, cycle, evaluation (published), rating, demand.
    Return (token, charity_id, cycle_id, eval_id).
    """
    await client.post("/auth/register", json={
        "email": "export_admin@test.com", "password": "testpass123",
        "full_name": "Export Admin", "role": "admin",
    })
    login = await client.post("/auth/login", json={
        "email": "export_admin@test.com", "password": "testpass123",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Charity
    charity = await client.post("/charities/", json={
        "cra_number": "888888801RR0001", "formal_name": "Export Test Charity",
    }, headers=headers)
    charity_id = charity.json()["id"]

    # Cycle
    cycle = await client.post("/cycles/", json={"name": "Export Cycle"}, headers=headers)
    cycle_id = cycle.json()["id"]

    # Evaluation — advance to published stage
    eval_resp = await client.post("/evaluations/", json={
        "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=headers)
    eval_id = eval_resp.json()["id"]

    # Walk through all stages to reach published
    stages = [
        "assigned", "financials_acquisition", "federal_corp_check",
        "cra_data_pull", "financial_analysis", "srss_scoring",
        "impact_scoring", "review", "charity_outreach",
        "charity_response", "published",
    ]
    for stage in stages:
        await client.post(f"/evaluations/{eval_id}/transition", json={
            "to_stage": stage,
        }, headers=headers)

    return token, charity_id, cycle_id, eval_id


def _api_key_headers():
    return {"X-API-Key": API_KEY}


# --- Published evaluations ---

@pytest.mark.asyncio
async def test_get_published_evaluations(client):
    _, charity_id, _, _ = await _setup(client)
    resp = await client.get(
        "/api/v1/evaluations/published",
        headers=_api_key_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    pub = [e for e in data if e["charity_id"] == charity_id]
    assert len(pub) == 1
    assert pub[0]["business_number"] == "888888801RR0001"
    assert pub[0]["formal_name"] == "Export Test Charity"


@pytest.mark.asyncio
async def test_published_requires_api_key(client):
    resp = await client.get("/api/v1/evaluations/published")
    assert resp.status_code in (401, 403, 422)


@pytest.mark.asyncio
async def test_published_rejects_wrong_key(client):
    resp = await client.get(
        "/api/v1/evaluations/published",
        headers={"X-API-Key": "wrong-key"},
    )
    assert resp.status_code == 401


# --- Incremental sync ---

@pytest.mark.asyncio
async def test_updated_since(client):
    _, _, _, _ = await _setup(client)
    resp = await client.get(
        "/api/v1/evaluations/updated-since",
        params={"since": "2020-01-01T00:00:00"},
        headers=_api_key_headers(),
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_updated_since_future(client):
    await _setup(client)
    resp = await client.get(
        "/api/v1/evaluations/updated-since",
        params={"since": "2099-01-01T00:00:00"},
        headers=_api_key_headers(),
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 0


# --- Demand signals ---

@pytest.mark.asyncio
async def test_demand_signals(client):
    token, charity_id, _, _ = await _setup(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create a demand entry: submit a public request that matches the charity
    await client.post("/demand/requests", json={
        "requester_name": "Test Donor",
        "requester_email": "donor@test.com",
        "requested_charity_name": "Export Test Charity",
    })

    resp = await client.get(
        "/api/v1/demand/signals",
        headers=_api_key_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_demand_signals_requires_api_key(client):
    resp = await client.get("/api/v1/demand/signals")
    assert resp.status_code in (401, 403, 422)
