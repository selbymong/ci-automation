import pytest


async def _setup(client):
    """Create user + charity. Return (token, user_id, charity_id)."""
    await client.post("/auth/register", json={
        "email": "note_admin@test.com", "password": "testpass123",
        "full_name": "Note Admin", "role": "admin",
    })
    login = await client.post("/auth/login", json={
        "email": "note_admin@test.com", "password": "testpass123",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = await client.get("/auth/me", headers=headers)
    user_id = me.json()["id"]

    charity = await client.post("/charities/", json={
        "cra_number": "800800801RR0001", "formal_name": "Note Test Charity",
    }, headers=headers)
    charity_id = charity.json()["id"]

    return token, user_id, charity_id


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_note(client):
    token, user_id, charity_id = await _setup(client)
    resp = await client.post("/notes/", json={
        "charity_id": charity_id, "content": "Test note content",
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["charity_id"] == charity_id
    assert data["content"] == "Test note content"
    assert data["note_type"] == "general"
    assert data["author_id"] == user_id


@pytest.mark.asyncio
async def test_create_note_with_type(client):
    token, _, charity_id = await _setup(client)
    resp = await client.post("/notes/", json={
        "charity_id": charity_id,
        "content": "Financial note",
        "note_type": "financial",
    }, headers=_auth(token))
    assert resp.status_code == 201
    assert resp.json()["note_type"] == "financial"


@pytest.mark.asyncio
async def test_create_note_invalid_type(client):
    token, _, charity_id = await _setup(client)
    resp = await client.post("/notes/", json={
        "charity_id": charity_id,
        "content": "Bad type",
        "note_type": "invalid_type",
    }, headers=_auth(token))
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_notes_for_charity(client):
    token, _, charity_id = await _setup(client)
    headers = _auth(token)
    await client.post("/notes/", json={
        "charity_id": charity_id, "content": "Note 1",
    }, headers=headers)
    await client.post("/notes/", json={
        "charity_id": charity_id, "content": "Note 2", "note_type": "financial",
    }, headers=headers)

    resp = await client.get(f"/notes/charity/{charity_id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_list_notes_filter_by_type(client):
    token, _, charity_id = await _setup(client)
    headers = _auth(token)
    await client.post("/notes/", json={
        "charity_id": charity_id, "content": "General note",
    }, headers=headers)
    await client.post("/notes/", json={
        "charity_id": charity_id, "content": "Financial note",
        "note_type": "financial",
    }, headers=headers)

    resp = await client.get(
        f"/notes/charity/{charity_id}?note_type=financial", headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["note_type"] == "financial"


@pytest.mark.asyncio
async def test_search_notes(client):
    token, _, charity_id = await _setup(client)
    headers = _auth(token)
    await client.post("/notes/", json={
        "charity_id": charity_id, "content": "Alpha bravo unique search term",
    }, headers=headers)

    resp = await client.get("/notes/search?q=unique search term", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    assert "unique search term" in resp.json()[0]["content"]


@pytest.mark.asyncio
async def test_search_notes_min_length(client):
    token, _, _ = await _setup(client)
    resp = await client.get("/notes/search?q=a", headers=_auth(token))
    assert resp.status_code == 422  # validation error, min_length=2


@pytest.mark.asyncio
async def test_update_note(client):
    token, _, charity_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/notes/", json={
        "charity_id": charity_id, "content": "Original content",
    }, headers=headers)
    note_id = create.json()["id"]

    resp = await client.put(f"/notes/{note_id}", json={
        "content": "Updated content",
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["content"] == "Updated content"


@pytest.mark.asyncio
async def test_update_note_not_found(client):
    token, _, _ = await _setup(client)
    resp = await client.put("/notes/nonexistent", json={
        "content": "X",
    }, headers=_auth(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_note_wrong_author(client):
    token, _, charity_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/notes/", json={
        "charity_id": charity_id, "content": "Original",
    }, headers=headers)
    note_id = create.json()["id"]

    # Create a second user
    await client.post("/auth/register", json={
        "email": "note_other@test.com", "password": "testpass123",
        "full_name": "Other User", "role": "analyst",
    })
    other_login = await client.post("/auth/login", json={
        "email": "note_other@test.com", "password": "testpass123",
    })
    other_token = other_login.json()["access_token"]

    resp = await client.put(f"/notes/{note_id}", json={
        "content": "Hacked!",
    }, headers=_auth(other_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_rejected(client):
    resp = await client.post("/notes/", json={
        "charity_id": "x", "content": "nope",
    })
    assert resp.status_code in (401, 403)
