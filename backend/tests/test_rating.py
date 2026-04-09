import pytest

from app.routers.rating import calculate_impact_coordinates, calculate_star_rating


async def _setup(client):
    """Create user + charity. Return (token, charity_id)."""
    await client.post("/auth/register", json={
        "email": "rating_admin@test.com", "password": "testpass123",
        "full_name": "Rating Admin", "role": "admin",
    })
    login = await client.post("/auth/login", json={
        "email": "rating_admin@test.com", "password": "testpass123",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    charity = await client.post("/charities/", json={
        "cra_number": "930930901RR0001", "formal_name": "Rating Test Charity",
    }, headers=headers)
    charity_id = charity.json()["id"]

    return token, charity_id


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# Unit tests for rating algorithms

def test_star_rating_5_stars():
    # Low overhead, strong reserves, high SRSS
    assert calculate_star_rating(10.0, 1.5, 85.0) == 5


def test_star_rating_3_stars():
    assert calculate_star_rating(30.0, 0.5, 55.0) == 3


def test_star_rating_1_star():
    assert calculate_star_rating(60.0, 0.1, 30.0) == 1


def test_star_rating_none_when_all_none():
    assert calculate_star_rating(None, None, None) is None


def test_star_rating_partial_metrics():
    # Only overhead provided
    result = calculate_star_rating(10.0, None, None)
    assert result == 5


def test_impact_coordinates():
    x, y, label = calculate_impact_coordinates(10.0, 85.0)
    assert x == 9.0  # (100-10)/10
    assert y == 8.5  # 85/10
    assert label == "High Impact, High Efficiency"


def test_impact_low_efficiency():
    x, y, label = calculate_impact_coordinates(60.0, 85.0)
    assert x == 4.0
    assert label == "High Impact, Low Efficiency"


def test_impact_none_inputs():
    x, y, label = calculate_impact_coordinates(None, None)
    assert x is None
    assert y is None
    assert label is None


# Integration tests

@pytest.mark.asyncio
async def test_create_rating_with_auto_calculation(client):
    token, charity_id = await _setup(client)
    resp = await client.post("/ratings/", json={
        "charity_id": charity_id,
        "overhead_percent": 12.0,
        "program_cost_coverage": 1.2,
        "srss_score": 82.0,
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["star_rating"] == 5
    assert data["impact_x"] is not None
    assert data["impact_y"] is not None
    assert data["impact_label"] == "High Impact, High Efficiency"


@pytest.mark.asyncio
async def test_create_rating_without_metrics(client):
    token, charity_id = await _setup(client)
    resp = await client.post("/ratings/", json={
        "charity_id": charity_id,
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["star_rating"] is None
    assert data["impact_x"] is None


@pytest.mark.asyncio
async def test_get_rating(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/ratings/", json={
        "charity_id": charity_id, "overhead_percent": 20.0,
    }, headers=headers)
    rating_id = create.json()["id"]

    resp = await client.get(f"/ratings/{rating_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == rating_id


@pytest.mark.asyncio
async def test_update_rating_recalculates(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/ratings/", json={
        "charity_id": charity_id, "overhead_percent": 50.0, "srss_score": 30.0,
    }, headers=headers)
    rating_id = create.json()["id"]
    assert create.json()["star_rating"] == 1

    resp = await client.put(f"/ratings/{rating_id}", json={
        "overhead_percent": 10.0, "srss_score": 90.0,
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["star_rating"] == 5


@pytest.mark.asyncio
async def test_list_ratings_by_charity(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    await client.post("/ratings/", json={
        "charity_id": charity_id, "overhead_percent": 15.0,
    }, headers=headers)

    resp = await client.get(f"/ratings/charity/{charity_id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_unauthenticated_rejected(client):
    resp = await client.post("/ratings/", json={"charity_id": "x"})
    assert resp.status_code in (401, 403)
