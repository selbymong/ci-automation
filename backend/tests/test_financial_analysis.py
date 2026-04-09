import pytest


async def _setup(client):
    """Create user, charity. Return (token, charity_id)."""
    await client.post("/auth/register", json={
        "email": "fin_admin@test.com", "password": "testpass123",
        "full_name": "Fin Admin", "role": "admin",
    })
    login = await client.post("/auth/login", json={
        "email": "fin_admin@test.com", "password": "testpass123",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    charity = await client.post("/charities/", json={
        "cra_number": "900900901RR0001", "formal_name": "Financial Test Charity",
    }, headers=headers)
    charity_id = charity.json()["id"]

    return token, charity_id


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


SAMPLE_FINANCIALS = {
    "fiscal_year_end": "2024-03-31",
    "donations": 500000.0,
    "government_funding": 200000.0,
    "other_revenue": 50000.0,
    "total_revenue": 750000.0,
    "program_costs": 600000.0,
    "admin_costs": 75000.0,
    "fundraising_costs": 50000.0,
    "total_expenses": 725000.0,
    "total_assets": 1000000.0,
    "total_liabilities": 200000.0,
    "net_assets": 800000.0,
    "reserves": 300000.0,
}


@pytest.mark.asyncio
async def test_create_financial_analysis(client):
    token, charity_id = await _setup(client)
    resp = await client.post("/financial-analyses/", json={
        "charity_id": charity_id, **SAMPLE_FINANCIALS,
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["charity_id"] == charity_id
    assert data["donations"] == 500000.0
    assert data["year_number"] == 1


@pytest.mark.asyncio
async def test_derived_metrics_calculated(client):
    token, charity_id = await _setup(client)
    resp = await client.post("/financial-analyses/", json={
        "charity_id": charity_id, **SAMPLE_FINANCIALS,
    }, headers=_auth(token))
    data = resp.json()
    # admin_percent = 75000 / 725000 * 100 = 10.34
    assert data["admin_percent"] == pytest.approx(10.34, abs=0.01)
    # fundraising_percent = 50000 / 725000 * 100 = 6.90
    assert data["fundraising_percent"] == pytest.approx(6.90, abs=0.01)
    # overhead = admin + fundraising = 17.24
    assert data["overhead_percent"] == pytest.approx(17.24, abs=0.01)
    # PCC = reserves / program_costs = 300000 / 600000 = 0.5
    assert data["program_cost_coverage"] == pytest.approx(0.5, abs=0.01)


@pytest.mark.asyncio
async def test_derived_metrics_null_when_no_expenses(client):
    token, charity_id = await _setup(client)
    resp = await client.post("/financial-analyses/", json={
        "charity_id": charity_id,
        "fiscal_year_end": "2024-03-31",
        "donations": 100000.0,
    }, headers=_auth(token))
    data = resp.json()
    assert data["admin_percent"] is None
    assert data["fundraising_percent"] is None
    assert data["overhead_percent"] is None
    assert data["program_cost_coverage"] is None


@pytest.mark.asyncio
async def test_get_financial_analysis(client):
    token, charity_id = await _setup(client)
    create = await client.post("/financial-analyses/", json={
        "charity_id": charity_id, **SAMPLE_FINANCIALS,
    }, headers=_auth(token))
    fa_id = create.json()["id"]

    resp = await client.get(f"/financial-analyses/{fa_id}", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["id"] == fa_id


@pytest.mark.asyncio
async def test_get_not_found(client):
    token, _ = await _setup(client)
    resp = await client.get("/financial-analyses/nonexistent", headers=_auth(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_financial_analysis(client):
    token, charity_id = await _setup(client)
    create = await client.post("/financial-analyses/", json={
        "charity_id": charity_id, **SAMPLE_FINANCIALS,
    }, headers=_auth(token))
    fa_id = create.json()["id"]

    resp = await client.put(f"/financial-analyses/{fa_id}", json={
        "admin_costs": 100000.0,
    }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["admin_costs"] == 100000.0
    # Derived metrics recalculated: 100000 / 725000 * 100 = 13.79
    assert data["admin_percent"] == pytest.approx(13.79, abs=0.01)


@pytest.mark.asyncio
async def test_multi_year_entry(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    await client.post("/financial-analyses/", json={
        "charity_id": charity_id, "fiscal_year_end": "2022-03-31",
        "year_number": 1, "donations": 400000.0, "total_expenses": 380000.0,
        "admin_costs": 40000.0, "fundraising_costs": 20000.0,
        "program_costs": 320000.0,
    }, headers=headers)
    await client.post("/financial-analyses/", json={
        "charity_id": charity_id, "fiscal_year_end": "2023-03-31",
        "year_number": 2, "donations": 450000.0, "total_expenses": 420000.0,
        "admin_costs": 45000.0, "fundraising_costs": 25000.0,
        "program_costs": 350000.0,
    }, headers=headers)
    await client.post("/financial-analyses/", json={
        "charity_id": charity_id, "fiscal_year_end": "2024-03-31",
        "year_number": 3, "donations": 500000.0, "total_expenses": 480000.0,
        "admin_costs": 50000.0, "fundraising_costs": 30000.0,
        "program_costs": 400000.0,
    }, headers=headers)

    resp = await client.get(
        f"/financial-analyses/charity/{charity_id}", headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert [d["year_number"] for d in data] == [1, 2, 3]


@pytest.mark.asyncio
async def test_financial_summary(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    await client.post("/financial-analyses/", json={
        "charity_id": charity_id, "fiscal_year_end": "2024-03-31",
        "donations": 500000.0, "total_expenses": 400000.0,
        "admin_costs": 40000.0, "fundraising_costs": 20000.0,
        "program_costs": 340000.0,
    }, headers=headers)

    resp = await client.get(
        f"/financial-analyses/charity/{charity_id}/summary", headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["charity_id"] == charity_id
    assert len(data["years"]) == 1


@pytest.mark.asyncio
async def test_unauthenticated_rejected(client):
    resp = await client.post("/financial-analyses/", json={
        "charity_id": "x", "fiscal_year_end": "2024-03-31",
    })
    assert resp.status_code in (401, 403)
