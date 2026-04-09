import pytest


async def _setup(client):
    """Create user + charity. Return (token, charity_id)."""
    await client.post("/auth/register", json={
        "email": "transp_admin@test.com", "password": "testpass123",
        "full_name": "Transp Admin", "role": "admin",
    })
    login = await client.post("/auth/login", json={
        "email": "transp_admin@test.com", "password": "testpass123",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    charity = await client.post("/charities/", json={
        "cra_number": "910910901RR0001", "formal_name": "Transparency Test Charity",
    }, headers=headers)
    charity_id = charity.json()["id"]

    return token, charity_id


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_transparency_config(client):
    token, charity_id = await _setup(client)
    resp = await client.post("/transparency/", json={
        "charity_id": charity_id,
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["charity_id"] == charity_id
    # Default: 16 core flags true, 14 extended flags false => 16 true => score 2
    assert data["transparency_score"] == 2


@pytest.mark.asyncio
async def test_duplicate_config_rejected(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    await client.post("/transparency/", json={"charity_id": charity_id}, headers=headers)
    resp = await client.post("/transparency/", json={"charity_id": charity_id}, headers=headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_config(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    await client.post("/transparency/", json={"charity_id": charity_id}, headers=headers)

    resp = await client.get(f"/transparency/charity/{charity_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["charity_id"] == charity_id


@pytest.mark.asyncio
async def test_get_config_not_found(client):
    token, _ = await _setup(client)
    resp = await client.get("/transparency/charity/nonexistent", headers=_auth(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_config_increases_score(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    await client.post("/transparency/", json={"charity_id": charity_id}, headers=headers)

    # Enable enough extended flags to reach score 3 (need 20+ total)
    resp = await client.put(f"/transparency/charity/{charity_id}", json={
        "show_compensation": True,
        "show_endowment": True,
        "show_capital_assets": True,
        "show_pension": True,
    }, headers=headers)
    assert resp.status_code == 200
    # Now 16 + 4 = 20 flags true => score 3
    assert resp.json()["transparency_score"] == 3


@pytest.mark.asyncio
async def test_update_config_decreases_score(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    await client.post("/transparency/", json={"charity_id": charity_id}, headers=headers)

    # Disable enough core flags to drop to score 1
    resp = await client.put(f"/transparency/charity/{charity_id}", json={
        "show_donations": False,
        "show_government_funding": False,
        "show_other_revenue": False,
        "show_total_revenue": False,
        "show_program_costs": False,
        "show_admin_costs": False,
        "show_fundraising_costs": False,
    }, headers=headers)
    assert resp.status_code == 200
    # 16 - 7 = 9 flags true => score 1
    assert resp.json()["transparency_score"] == 1


@pytest.mark.asyncio
async def test_unauthenticated_rejected(client):
    resp = await client.post("/transparency/", json={"charity_id": "x"})
    assert resp.status_code in (401, 403)
