"""Tests for F070 (T3010 data retrieval) and F071 (scraped data retrieval)."""

import pytest


async def _setup(client):
    """Create admin + charity, return (token, charity_id, cra_number)."""
    await client.post("/auth/register", json={
        "email": "harness_admin@test.com", "password": "testpass123",
        "full_name": "Harness Admin", "role": "admin",
    })
    login = await client.post("/auth/login", json={
        "email": "harness_admin@test.com", "password": "testpass123",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cra_number = "899899901RR0001"
    charity = await client.post("/charities/", json={
        "cra_number": cra_number, "formal_name": "Harness Test Charity",
    }, headers=headers)
    charity_id = charity.json()["id"]

    return token, charity_id, cra_number


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# --- F070: T3010 data ---

@pytest.mark.asyncio
async def test_get_t3010_by_charity(client):
    token, charity_id, cra = await _setup(client)
    resp = await client.get(f"/harness/t3010/{charity_id}", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["business_number"] == cra
    assert data["revenue_total"] == 5_000_000.0
    assert data["expenses_total"] == 4_800_000.0


@pytest.mark.asyncio
async def test_get_t3010_by_bn(client):
    token, _, cra = await _setup(client)
    resp = await client.get(f"/harness/t3010/bn/{cra}", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["business_number"] == cra


@pytest.mark.asyncio
async def test_t3010_unauthenticated(client):
    resp = await client.get("/harness/t3010/bn/123456789RR0001")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_t3010_charity_not_found(client):
    token, _, _ = await _setup(client)
    resp = await client.get(
        "/harness/t3010/00000000-0000-0000-0000-000000000000",
        headers=_auth(token),
    )
    assert resp.status_code == 404


# --- F071: Scraped data ---

@pytest.mark.asyncio
async def test_get_scraped_by_charity(client):
    token, charity_id, cra = await _setup(client)
    resp = await client.get(f"/harness/scrape/{charity_id}", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["business_number"] == cra
    assert data["has_new_financial_statements"] is True
    assert "annual_report_url" in data


@pytest.mark.asyncio
async def test_get_scraped_by_bn(client):
    token, _, cra = await _setup(client)
    resp = await client.get(f"/harness/scrape/bn/{cra}", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["business_number"] == cra


@pytest.mark.asyncio
async def test_scraped_unauthenticated(client):
    resp = await client.get("/harness/scrape/bn/123456789RR0001")
    assert resp.status_code in (401, 403)


# --- Organization lookup ---

@pytest.mark.asyncio
async def test_get_organization(client):
    token, charity_id, cra = await _setup(client)
    resp = await client.get(f"/harness/organization/{charity_id}", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["business_number"] == cra
    assert data["status"] == "registered"
