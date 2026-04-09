import pytest


async def _register_and_login(client, email, role="analyst"):
    await client.post("/auth/register", json={
        "email": email,
        "password": "testpass123",
        "full_name": f"Test {role.title()}",
        "role": role,
    })
    resp = await client.post("/auth/login", json={
        "email": email, "password": "testpass123",
    })
    return resp.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_sector_group_admin(client):
    token = await _register_and_login(client, "admin@test.com", "admin")
    resp = await client.post("/sectors/groups", json={
        "name": "Social Services",
        "description": "Organizations providing social services",
    }, headers=_auth(token))
    assert resp.status_code == 201
    assert resp.json()["name"] == "Social Services"


@pytest.mark.asyncio
async def test_create_sector_group_non_admin_forbidden(client):
    token = await _register_and_login(client, "analyst@test.com", "analyst")
    resp = await client.post("/sectors/groups", json={
        "name": "Health",
    }, headers=_auth(token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_sector_group_duplicate(client):
    token = await _register_and_login(client, "admin@test.com", "admin")
    await client.post("/sectors/groups", json={"name": "Dup Group"}, headers=_auth(token))
    resp = await client.post("/sectors/groups", json={"name": "Dup Group"}, headers=_auth(token))
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_sector(client):
    token = await _register_and_login(client, "admin@test.com", "admin")
    resp = await client.post("/sectors/", json={
        "name": "International Aid",
    }, headers=_auth(token))
    assert resp.status_code == 201
    assert resp.json()["name"] == "International Aid"


@pytest.mark.asyncio
async def test_create_sector_with_group(client):
    token = await _register_and_login(client, "admin@test.com", "admin")
    group_resp = await client.post("/sectors/groups", json={"name": "Health Group"}, headers=_auth(token))
    group_id = group_resp.json()["id"]
    resp = await client.post("/sectors/", json={
        "name": "Mental Health",
        "group_id": group_id,
    }, headers=_auth(token))
    assert resp.status_code == 201
    assert resp.json()["group_id"] == group_id


@pytest.mark.asyncio
async def test_create_sub_sector(client):
    token = await _register_and_login(client, "admin@test.com", "admin")
    sector_resp = await client.post("/sectors/", json={"name": "Education"}, headers=_auth(token))
    sector_id = sector_resp.json()["id"]
    resp = await client.post("/sectors/sub-sectors", json={
        "name": "K-12",
        "sector_id": sector_id,
    }, headers=_auth(token))
    assert resp.status_code == 201
    assert resp.json()["name"] == "K-12"


@pytest.mark.asyncio
async def test_list_sectors(client):
    token = await _register_and_login(client, "admin@test.com", "admin")
    await client.post("/sectors/", json={"name": "Sector A"}, headers=_auth(token))
    await client.post("/sectors/", json={"name": "Sector B"}, headers=_auth(token))

    analyst_token = await _register_and_login(client, "analyst@test.com", "analyst")
    resp = await client.get("/sectors/", headers=_auth(analyst_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_list_sector_groups_with_sectors(client):
    token = await _register_and_login(client, "admin@test.com", "admin")
    group_resp = await client.post("/sectors/groups", json={"name": "Test Group"}, headers=_auth(token))
    group_id = group_resp.json()["id"]
    await client.post("/sectors/", json={"name": "In Group Sector", "group_id": group_id}, headers=_auth(token))

    resp = await client.get("/sectors/groups", headers=_auth(token))
    assert resp.status_code == 200
    groups = resp.json()
    assert len(groups) == 1
    assert len(groups[0]["sectors"]) == 1


@pytest.mark.asyncio
async def test_assign_sector_to_charity(client):
    token = await _register_and_login(client, "user@test.com", "analyst")
    charity_resp = await client.post("/charities/", json={
        "cra_number": "111111111RR0001",
        "formal_name": "Test Charity",
    }, headers=_auth(token))
    charity_id = charity_resp.json()["id"]

    resp = await client.put(f"/sectors/charities/{charity_id}/sector", json={
        "sector": "Health",
        "sub_sector": "Mental Health",
    }, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["sector"] == "Health"
    assert resp.json()["sub_sector"] == "Mental Health"

    # Verify it persisted
    get_resp = await client.get(f"/charities/{charity_id}", headers=_auth(token))
    assert get_resp.json()["sector"] == "Health"
    assert get_resp.json()["sub_sector"] == "Mental Health"
