import pytest


async def _setup(client):
    """Create user + charity. Return (token, charity_id)."""
    await client.post("/auth/register", json={
        "email": "profile_admin@test.com", "password": "testpass123",
        "full_name": "Profile Admin", "role": "admin",
    })
    login = await client.post("/auth/login", json={
        "email": "profile_admin@test.com", "password": "testpass123",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    charity = await client.post("/charities/", json={
        "cra_number": "950950901RR0001", "formal_name": "Profile Test Charity",
    }, headers=headers)
    charity_id = charity.json()["id"]

    return token, charity_id


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_content(client):
    token, charity_id = await _setup(client)
    resp = await client.post("/profile-content/", json={
        "charity_id": charity_id,
        "section_type": "results_impact",
        "content": "<p>This charity has high impact...</p>",
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["section_type"] == "results_impact"
    assert data["version"] == 1


@pytest.mark.asyncio
async def test_create_content_invalid_type(client):
    token, charity_id = await _setup(client)
    resp = await client.post("/profile-content/", json={
        "charity_id": charity_id,
        "section_type": "invalid_section",
        "content": "bad",
    }, headers=_auth(token))
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_creates_new_version(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/profile-content/", json={
        "charity_id": charity_id,
        "section_type": "results_impact",
        "content": "Version 1 content",
    }, headers=headers)
    content_id = create.json()["id"]

    resp = await client.put(f"/profile-content/{content_id}", json={
        "content": "Version 2 content - updated",
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == 2
    assert data["content"] == "Version 2 content - updated"
    # New ID (new record)
    assert data["id"] != content_id


@pytest.mark.asyncio
async def test_list_content_shows_all_versions(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/profile-content/", json={
        "charity_id": charity_id,
        "section_type": "mission",
        "content": "Mission v1",
    }, headers=headers)
    content_id = create.json()["id"]
    await client.put(f"/profile-content/{content_id}", json={
        "content": "Mission v2",
    }, headers=headers)

    resp = await client.get(f"/profile-content/charity/{charity_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_content(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/profile-content/", json={
        "charity_id": charity_id,
        "section_type": "financial_review",
        "content": "Review content",
    }, headers=headers)
    content_id = create.json()["id"]

    resp = await client.get(f"/profile-content/{content_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["content"] == "Review content"


@pytest.mark.asyncio
async def test_get_content_not_found(client):
    token, _ = await _setup(client)
    resp = await client.get("/profile-content/nonexistent", headers=_auth(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_html_content_stored(client):
    token, charity_id = await _setup(client)
    html = "<h2>Results</h2><p>The charity has demonstrated <strong>significant impact</strong> in...</p>"
    resp = await client.post("/profile-content/", json={
        "charity_id": charity_id,
        "section_type": "results_impact",
        "content": html,
    }, headers=_auth(token))
    assert resp.status_code == 201
    assert resp.json()["content"] == html


@pytest.mark.asyncio
async def test_unauthenticated_rejected(client):
    resp = await client.post("/profile-content/", json={
        "charity_id": "x", "section_type": "mission", "content": "nope",
    })
    assert resp.status_code in (401, 403)
