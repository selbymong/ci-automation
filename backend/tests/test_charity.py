import pytest


async def _get_token(client, email="testuser@test.com"):
    """Helper: register + login, return bearer token."""
    await client.post("/auth/register", json={
        "email": email,
        "password": "testpass123",
        "full_name": "Test User",
        "role": "analyst",
    })
    resp = await client.post("/auth/login", json={
        "email": email,
        "password": "testpass123",
    })
    return resp.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


SAMPLE_CHARITY = {
    "cra_number": "119219814RR0001",
    "formal_name": "Canadian Red Cross Society",
    "common_name": "Red Cross Canada",
    "sector": "International Aid",
    "website": "https://www.redcross.ca",
    "city": "Ottawa",
    "province": "ON",
    "is_top_100": True,
}


@pytest.mark.asyncio
async def test_create_charity(client):
    token = await _get_token(client)
    resp = await client.post("/charities/", json=SAMPLE_CHARITY, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["cra_number"] == "119219814RR0001"
    assert data["formal_name"] == "Canadian Red Cross Society"
    assert data["common_name"] == "Red Cross Canada"
    assert data["is_top_100"] is True
    assert data["id"]


@pytest.mark.asyncio
async def test_create_charity_duplicate_cra(client):
    token = await _get_token(client)
    await client.post("/charities/", json=SAMPLE_CHARITY, headers=_auth(token))
    resp = await client.post("/charities/", json=SAMPLE_CHARITY, headers=_auth(token))
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_charity_unauthenticated(client):
    resp = await client.post("/charities/", json=SAMPLE_CHARITY)
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_charity(client):
    token = await _get_token(client)
    create_resp = await client.post("/charities/", json=SAMPLE_CHARITY, headers=_auth(token))
    charity_id = create_resp.json()["id"]
    resp = await client.get(f"/charities/{charity_id}", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["cra_number"] == "119219814RR0001"


@pytest.mark.asyncio
async def test_get_charity_not_found(client):
    token = await _get_token(client)
    resp = await client.get("/charities/nonexistent-id", headers=_auth(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_charities(client):
    token = await _get_token(client)
    await client.post("/charities/", json=SAMPLE_CHARITY, headers=_auth(token))
    await client.post("/charities/", json={
        **SAMPLE_CHARITY,
        "cra_number": "123456789RR0001",
        "formal_name": "Another Charity",
    }, headers=_auth(token))
    resp = await client.get("/charities/", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_search_charities_by_name(client):
    token = await _get_token(client)
    await client.post("/charities/", json=SAMPLE_CHARITY, headers=_auth(token))
    await client.post("/charities/", json={
        **SAMPLE_CHARITY,
        "cra_number": "999999999RR0001",
        "formal_name": "Doctors Without Borders Canada",
        "common_name": "MSF Canada",
        "sector": "Health",
    }, headers=_auth(token))

    resp = await client.get("/charities/?search=Red Cross", headers=_auth(token))
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["formal_name"] == "Canadian Red Cross Society"


@pytest.mark.asyncio
async def test_search_charities_by_cra(client):
    token = await _get_token(client)
    await client.post("/charities/", json=SAMPLE_CHARITY, headers=_auth(token))
    resp = await client.get("/charities/?search=119219814", headers=_auth(token))
    data = resp.json()
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_filter_charities_by_sector(client):
    token = await _get_token(client)
    await client.post("/charities/", json=SAMPLE_CHARITY, headers=_auth(token))
    await client.post("/charities/", json={
        **SAMPLE_CHARITY,
        "cra_number": "888888888RR0001",
        "formal_name": "Health Org",
        "sector": "Health",
    }, headers=_auth(token))

    resp = await client.get("/charities/?sector=Health", headers=_auth(token))
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["sector"] == "Health"


@pytest.mark.asyncio
async def test_update_charity(client):
    token = await _get_token(client)
    create_resp = await client.post("/charities/", json=SAMPLE_CHARITY, headers=_auth(token))
    charity_id = create_resp.json()["id"]
    resp = await client.put(f"/charities/{charity_id}", json={
        "common_name": "Red Cross",
        "website": "https://redcross.ca",
    }, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["common_name"] == "Red Cross"
    assert resp.json()["website"] == "https://redcross.ca"
    # Unchanged fields should persist
    assert resp.json()["formal_name"] == "Canadian Red Cross Society"


@pytest.mark.asyncio
async def test_delete_charity_soft(client):
    token = await _get_token(client)
    create_resp = await client.post("/charities/", json=SAMPLE_CHARITY, headers=_auth(token))
    charity_id = create_resp.json()["id"]
    del_resp = await client.delete(f"/charities/{charity_id}", headers=_auth(token))
    assert del_resp.status_code == 204
    # Should no longer be visible
    get_resp = await client.get(f"/charities/{charity_id}", headers=_auth(token))
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_list_pagination(client):
    token = await _get_token(client)
    for i in range(5):
        await client.post("/charities/", json={
            **SAMPLE_CHARITY,
            "cra_number": f"{100000000 + i}RR0001",
            "formal_name": f"Charity {i:03d}",
        }, headers=_auth(token))
    resp = await client.get("/charities/?skip=2&limit=2", headers=_auth(token))
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
