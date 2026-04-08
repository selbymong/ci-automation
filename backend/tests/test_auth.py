import pytest


@pytest.mark.asyncio
async def test_register_analyst(client):
    response = await client.post("/auth/register", json={
        "email": "analyst@test.com",
        "password": "testpass123",
        "full_name": "Test Analyst",
        "role": "analyst",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "analyst@test.com"
    assert data["role"] == "analyst"
    assert data["full_name"] == "Test Analyst"
    assert data["is_active"] is True
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_reviewer(client):
    response = await client.post("/auth/register", json={
        "email": "reviewer@test.com",
        "password": "testpass123",
        "full_name": "Test Reviewer",
        "role": "reviewer",
    })
    assert response.status_code == 201
    assert response.json()["role"] == "reviewer"


@pytest.mark.asyncio
async def test_register_admin(client):
    response = await client.post("/auth/register", json={
        "email": "admin@test.com",
        "password": "testpass123",
        "full_name": "Test Admin",
        "role": "admin",
    })
    assert response.status_code == 201
    assert response.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post("/auth/register", json={
        "email": "dup@test.com",
        "password": "testpass123",
        "full_name": "First User",
        "role": "analyst",
    })
    response = await client.post("/auth/register", json={
        "email": "dup@test.com",
        "password": "testpass123",
        "full_name": "Second User",
        "role": "analyst",
    })
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_invalid_role(client):
    response = await client.post("/auth/register", json={
        "email": "bad@test.com",
        "password": "testpass123",
        "full_name": "Bad Role",
        "role": "superadmin",
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/auth/register", json={
        "email": "login@test.com",
        "password": "testpass123",
        "full_name": "Login User",
        "role": "analyst",
    })
    response = await client.post("/auth/login", json={
        "email": "login@test.com",
        "password": "testpass123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/auth/register", json={
        "email": "wrongpw@test.com",
        "password": "testpass123",
        "full_name": "Wrong PW",
        "role": "analyst",
    })
    response = await client.post("/auth/login", json={
        "email": "wrongpw@test.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    response = await client.post("/auth/login", json={
        "email": "nobody@test.com",
        "password": "testpass123",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint(client):
    await client.post("/auth/register", json={
        "email": "me@test.com",
        "password": "testpass123",
        "full_name": "Me User",
        "role": "reviewer",
    })
    login_resp = await client.post("/auth/login", json={
        "email": "me@test.com",
        "password": "testpass123",
    })
    token = login_resp.json()["access_token"]
    response = await client.get("/auth/me", headers={
        "Authorization": f"Bearer {token}",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@test.com"
    assert data["role"] == "reviewer"


@pytest.mark.asyncio
async def test_me_unauthorized(client):
    response = await client.get("/auth/me")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_all_three_roles_authenticate(client):
    """Register and login as each role, then verify /auth/me returns correct role."""
    for role in ["analyst", "reviewer", "admin"]:
        email = f"auth3_{role}@test.com"
        await client.post("/auth/register", json={
            "email": email,
            "password": "testpass123",
            "full_name": f"Test {role.title()}",
            "role": role,
        })
        login_resp = await client.post("/auth/login", json={
            "email": email,
            "password": "testpass123",
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        me_resp = await client.get("/auth/me", headers={
            "Authorization": f"Bearer {token}",
        })
        assert me_resp.status_code == 200
        assert me_resp.json()["role"] == role
