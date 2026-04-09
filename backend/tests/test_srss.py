import pytest

from app.models.srss import percentage_to_grade


async def _setup(client):
    """Create user + charity. Return (token, charity_id)."""
    await client.post("/auth/register", json={
        "email": "srss_admin@test.com", "password": "testpass123",
        "full_name": "SRSS Admin", "role": "admin",
    })
    login = await client.post("/auth/login", json={
        "email": "srss_admin@test.com", "password": "testpass123",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    charity = await client.post("/charities/", json={
        "cra_number": "940940901RR0001", "formal_name": "SRSS Test Charity",
    }, headers=headers)
    charity_id = charity.json()["id"]

    return token, charity_id


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# Unit tests for grade calculation

def test_grade_a_plus():
    assert percentage_to_grade(95.0) == "A+"


def test_grade_a():
    assert percentage_to_grade(85.0) == "A"


def test_grade_b_plus():
    assert percentage_to_grade(75.0) == "B+"


def test_grade_b():
    assert percentage_to_grade(65.0) == "B"


def test_grade_c():
    assert percentage_to_grade(55.0) == "C"


def test_grade_d():
    assert percentage_to_grade(45.0) == "D"


def test_grade_f():
    assert percentage_to_grade(35.0) == "F"


# All 26 questions scored 8/8 = 100% = A+
PERFECT_SCORES = {f"q{i}": 8 for i in range(1, 27)}

# Partial scores: only strategy questions (Q1-Q4) filled
PARTIAL_SCORES = {"q1": 6, "q2": 7, "q3": 5, "q4": 8}


@pytest.mark.asyncio
async def test_create_srss_perfect_score(client):
    token, charity_id = await _setup(client)
    resp = await client.post("/srss/", json={
        "charity_id": charity_id, "year": 2025, **PERFECT_SCORES,
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["total_pct"] == 100.0
    assert data["letter_grade"] == "A+"
    assert data["strategy_pct"] == 100.0
    assert data["activities_pct"] == 100.0


@pytest.mark.asyncio
async def test_create_srss_partial_scores(client):
    token, charity_id = await _setup(client)
    resp = await client.post("/srss/", json={
        "charity_id": charity_id, "year": 2025, **PARTIAL_SCORES,
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    # Strategy: (6+7+5+8) / (8*4) * 100 = 26/32 * 100 = 81.25
    assert data["strategy_pct"] == pytest.approx(81.25, abs=0.01)
    # Other categories should be None since no questions answered
    assert data["activities_pct"] is None
    # Total: 26 / 32 * 100 = 81.25
    assert data["total_pct"] == pytest.approx(81.25, abs=0.01)
    assert data["letter_grade"] == "A"


@pytest.mark.asyncio
async def test_create_srss_no_scores(client):
    token, charity_id = await _setup(client)
    resp = await client.post("/srss/", json={
        "charity_id": charity_id, "year": 2025,
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["total_pct"] is None
    assert data["letter_grade"] is None


@pytest.mark.asyncio
async def test_get_srss_score(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/srss/", json={
        "charity_id": charity_id, "year": 2025, "q1": 6,
    }, headers=headers)
    score_id = create.json()["id"]

    resp = await client.get(f"/srss/{score_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == score_id


@pytest.mark.asyncio
async def test_update_srss_recalculates(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/srss/", json={
        "charity_id": charity_id, "year": 2025, "q1": 4,
    }, headers=headers)
    score_id = create.json()["id"]

    resp = await client.put(f"/srss/{score_id}", json={
        "q1": 8, "q2": 8, "q3": 8, "q4": 8,
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["strategy_pct"] == 100.0


@pytest.mark.asyncio
async def test_list_by_charity(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    await client.post("/srss/", json={
        "charity_id": charity_id, "year": 2024, "q1": 5,
    }, headers=headers)
    await client.post("/srss/", json={
        "charity_id": charity_id, "year": 2025, "q1": 7,
    }, headers=headers)

    resp = await client.get(f"/srss/charity/{charity_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    # Sorted by year desc
    assert data[0]["year"] == 2025
    assert data[1]["year"] == 2024


# Historical (F031)

@pytest.mark.asyncio
async def test_create_historical(client):
    token, charity_id = await _setup(client)
    resp = await client.post("/srss/historical", json={
        "charity_id": charity_id, "year": 2020,
        "total_pct": 72.5, "letter_grade": "B+",
    }, headers=_auth(token))
    assert resp.status_code == 201
    assert resp.json()["year"] == 2020
    assert resp.json()["letter_grade"] == "B+"


@pytest.mark.asyncio
async def test_list_historical_trend(client):
    token, charity_id = await _setup(client)
    headers = _auth(token)
    for year, pct, grade in [(2018, 55.0, "C"), (2019, 62.0, "B"), (2020, 70.0, "B+")]:
        await client.post("/srss/historical", json={
            "charity_id": charity_id, "year": year,
            "total_pct": pct, "letter_grade": grade,
        }, headers=headers)

    resp = await client.get(f"/srss/historical/{charity_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    # Sorted by year asc
    assert data[0]["year"] == 2018
    assert data[2]["year"] == 2020
    # Verify trend is improving
    assert data[2]["total_pct"] > data[0]["total_pct"]


@pytest.mark.asyncio
async def test_unauthenticated_rejected(client):
    resp = await client.post("/srss/", json={
        "charity_id": "x", "year": 2025,
    })
    assert resp.status_code in (401, 403)
