import pytest


async def _setup(client):
    """Create admin, reviewer, charity, cycle, evaluation. Return (admin_token, reviewer_token, eval_id)."""
    # Admin
    await client.post("/auth/register", json={
        "email": "authz_admin@test.com", "password": "testpass123",
        "full_name": "Authz Admin", "role": "admin",
    })
    admin_login = await client.post("/auth/login", json={
        "email": "authz_admin@test.com", "password": "testpass123",
    })
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Reviewer
    await client.post("/auth/register", json={
        "email": "authz_reviewer@test.com", "password": "testpass123",
        "full_name": "Authz Reviewer", "role": "reviewer",
    })
    reviewer_login = await client.post("/auth/login", json={
        "email": "authz_reviewer@test.com", "password": "testpass123",
    })
    reviewer_token = reviewer_login.json()["access_token"]

    # Create charity + cycle + evaluation
    charity = await client.post("/charities/", json={
        "cra_number": "960960901RR0001", "formal_name": "Authz Test Charity",
    }, headers=admin_headers)
    cycle = await client.post("/cycles/", json={"name": "Authz Cycle"}, headers=admin_headers)
    eval_resp = await client.post("/evaluations/", json={
        "charity_id": charity.json()["id"], "cycle_id": cycle.json()["id"],
    }, headers=admin_headers)
    eval_id = eval_resp.json()["id"]

    return admin_token, reviewer_token, eval_id


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_authorization(client):
    admin_token, _, eval_id = await _setup(client)
    resp = await client.post("/authorizations/", json={
        "evaluation_id": eval_id, "step": "financial_review",
    }, headers=_auth(admin_token))
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"
    assert resp.json()["step"] == "financial_review"


@pytest.mark.asyncio
async def test_create_authorization_invalid_step(client):
    admin_token, _, eval_id = await _setup(client)
    resp = await client.post("/authorizations/", json={
        "evaluation_id": eval_id, "step": "invalid_step",
    }, headers=_auth(admin_token))
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_duplicate_pending_rejected(client):
    admin_token, _, eval_id = await _setup(client)
    headers = _auth(admin_token)
    await client.post("/authorizations/", json={
        "evaluation_id": eval_id, "step": "financial_review",
    }, headers=headers)
    resp = await client.post("/authorizations/", json={
        "evaluation_id": eval_id, "step": "financial_review",
    }, headers=headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_approve_authorization(client):
    admin_token, reviewer_token, eval_id = await _setup(client)
    create = await client.post("/authorizations/", json={
        "evaluation_id": eval_id, "step": "financial_review",
    }, headers=_auth(admin_token))
    auth_id = create.json()["id"]

    resp = await client.put(f"/authorizations/{auth_id}/decide", json={
        "status": "approved", "comment": "Looks good",
    }, headers=_auth(reviewer_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "approved"
    assert data["comment"] == "Looks good"
    assert data["decided_at"] is not None


@pytest.mark.asyncio
async def test_reject_authorization(client):
    admin_token, reviewer_token, eval_id = await _setup(client)
    create = await client.post("/authorizations/", json={
        "evaluation_id": eval_id, "step": "final_signoff",
    }, headers=_auth(admin_token))
    auth_id = create.json()["id"]

    resp = await client.put(f"/authorizations/{auth_id}/decide", json={
        "status": "rejected", "comment": "Needs revision",
    }, headers=_auth(reviewer_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_cannot_decide_twice(client):
    admin_token, reviewer_token, eval_id = await _setup(client)
    create = await client.post("/authorizations/", json={
        "evaluation_id": eval_id, "step": "financial_review",
    }, headers=_auth(admin_token))
    auth_id = create.json()["id"]

    await client.put(f"/authorizations/{auth_id}/decide", json={
        "status": "approved",
    }, headers=_auth(reviewer_token))
    resp = await client.put(f"/authorizations/{auth_id}/decide", json={
        "status": "rejected",
    }, headers=_auth(reviewer_token))
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_analyst_cannot_decide(client):
    admin_token, _, eval_id = await _setup(client)
    # Create analyst
    await client.post("/auth/register", json={
        "email": "authz_analyst@test.com", "password": "testpass123",
        "full_name": "Authz Analyst", "role": "analyst",
    })
    analyst_login = await client.post("/auth/login", json={
        "email": "authz_analyst@test.com", "password": "testpass123",
    })
    analyst_token = analyst_login.json()["access_token"]

    create = await client.post("/authorizations/", json={
        "evaluation_id": eval_id, "step": "financial_review",
    }, headers=_auth(admin_token))
    auth_id = create.json()["id"]

    resp = await client.put(f"/authorizations/{auth_id}/decide", json={
        "status": "approved",
    }, headers=_auth(analyst_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_authorizations(client):
    admin_token, _, eval_id = await _setup(client)
    headers = _auth(admin_token)
    await client.post("/authorizations/", json={
        "evaluation_id": eval_id, "step": "financial_review",
    }, headers=headers)
    await client.post("/authorizations/", json={
        "evaluation_id": eval_id, "step": "final_signoff",
    }, headers=headers)

    resp = await client.get(f"/authorizations/evaluation/{eval_id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_list_pending(client):
    admin_token, reviewer_token, eval_id = await _setup(client)
    await client.post("/authorizations/", json={
        "evaluation_id": eval_id, "step": "financial_review",
    }, headers=_auth(admin_token))

    resp = await client.get("/authorizations/pending", headers=_auth(reviewer_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_unauthenticated_rejected(client):
    resp = await client.post("/authorizations/", json={
        "evaluation_id": "x", "step": "financial_review",
    })
    assert resp.status_code in (401, 403)
