import pytest


async def _setup(client):
    """Register user, login, create a charity. Returns (token, charity_id)."""
    await client.post("/auth/register", json={
        "email": "contact_user@test.com",
        "password": "testpass123",
        "full_name": "Contact Tester",
        "role": "analyst",
    })
    login = await client.post("/auth/login", json={
        "email": "contact_user@test.com",
        "password": "testpass123",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    charity = await client.post("/charities/", json={
        "cra_number": "222222222RR0001",
        "formal_name": "Contact Test Charity",
    }, headers=headers)
    return token, charity.json()["id"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_contact(client):
    token, charity_id = await _setup(client)
    resp = await client.post("/contacts/", json={
        "charity_id": charity_id,
        "name": "Jane Smith",
        "email": "jane@charity.org",
        "phone": "613-555-1234",
        "role": "Executive Director",
        "notes": "Primary contact",
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Jane Smith"
    assert data["email"] == "jane@charity.org"
    assert data["charity_id"] == charity_id


@pytest.mark.asyncio
async def test_create_contact_invalid_charity(client):
    await client.post("/auth/register", json={
        "email": "bad_charity@test.com", "password": "testpass123",
        "full_name": "Test", "role": "analyst",
    })
    login = await client.post("/auth/login", json={
        "email": "bad_charity@test.com", "password": "testpass123",
    })
    token = login.json()["access_token"]
    resp = await client.post("/contacts/", json={
        "charity_id": "nonexistent",
        "name": "Nobody",
    }, headers=_auth(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_contacts_for_charity(client):
    token, charity_id = await _setup(client)
    await client.post("/contacts/", json={
        "charity_id": charity_id, "name": "Alice",
    }, headers=_auth(token))
    await client.post("/contacts/", json={
        "charity_id": charity_id, "name": "Bob",
    }, headers=_auth(token))
    resp = await client.get(f"/contacts/charity/{charity_id}", headers=_auth(token))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_contact(client):
    token, charity_id = await _setup(client)
    create = await client.post("/contacts/", json={
        "charity_id": charity_id, "name": "Get Test",
    }, headers=_auth(token))
    contact_id = create.json()["id"]
    resp = await client.get(f"/contacts/{contact_id}", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get Test"


@pytest.mark.asyncio
async def test_update_contact(client):
    token, charity_id = await _setup(client)
    create = await client.post("/contacts/", json={
        "charity_id": charity_id, "name": "Original Name", "email": "old@test.com",
    }, headers=_auth(token))
    contact_id = create.json()["id"]
    resp = await client.put(f"/contacts/{contact_id}", json={
        "name": "Updated Name",
        "phone": "416-555-9999",
    }, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"
    assert resp.json()["phone"] == "416-555-9999"
    assert resp.json()["email"] == "old@test.com"  # unchanged


@pytest.mark.asyncio
async def test_delete_contact(client):
    token, charity_id = await _setup(client)
    create = await client.post("/contacts/", json={
        "charity_id": charity_id, "name": "Delete Me",
    }, headers=_auth(token))
    contact_id = create.json()["id"]
    del_resp = await client.delete(f"/contacts/{contact_id}", headers=_auth(token))
    assert del_resp.status_code == 204
    get_resp = await client.get(f"/contacts/{contact_id}", headers=_auth(token))
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_contact_unauthenticated(client):
    resp = await client.post("/contacts/", json={
        "charity_id": "x", "name": "No Auth",
    })
    assert resp.status_code in (401, 403)
