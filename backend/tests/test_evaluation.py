import pytest

from app.models.evaluation import STAGE_ORDER


async def _setup(client):
    """Create admin, charity, cycle. Return (token, charity_id, cycle_id)."""
    await client.post("/auth/register", json={
        "email": "eval_user@test.com", "password": "testpass123",
        "full_name": "Eval User", "role": "admin",
    })
    resp = await client.post("/auth/login", json={
        "email": "eval_user@test.com", "password": "testpass123",
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    charity = await client.post("/charities/", json={
        "cra_number": "666666666RR0001", "formal_name": "Eval Charity",
    }, headers=headers)
    cycle = await client.post("/cycles/", json={"name": "Eval Cycle"}, headers=headers)
    return token, charity.json()["id"], cycle.json()["id"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_evaluation(client):
    token, charity_id, cycle_id = await _setup(client)
    resp = await client.post("/evaluations/", json={
        "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=_auth(token))
    assert resp.status_code == 201
    assert resp.json()["stage"] == "prioritized"


@pytest.mark.asyncio
async def test_create_evaluation_duplicate(client):
    token, charity_id, cycle_id = await _setup(client)
    headers = _auth(token)
    await client.post("/evaluations/", json={
        "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=headers)
    resp = await client.post("/evaluations/", json={
        "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_forward_transition(client):
    token, charity_id, cycle_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/evaluations/", json={
        "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=headers)
    eval_id = create.json()["id"]

    # prioritized -> assigned
    resp = await client.post(f"/evaluations/{eval_id}/transition", json={
        "to_stage": "assigned", "note": "Analyst assigned",
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["stage"] == "assigned"


@pytest.mark.asyncio
async def test_backward_transition_rejection(client):
    token, charity_id, cycle_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/evaluations/", json={
        "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=headers)
    eval_id = create.json()["id"]

    # Forward: prioritized -> assigned
    await client.post(f"/evaluations/{eval_id}/transition", json={
        "to_stage": "assigned",
    }, headers=headers)
    # Backward (rejection): assigned -> prioritized
    resp = await client.post(f"/evaluations/{eval_id}/transition", json={
        "to_stage": "prioritized", "note": "Rejected - wrong assignment",
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["stage"] == "prioritized"


@pytest.mark.asyncio
async def test_invalid_skip_transition(client):
    token, charity_id, cycle_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/evaluations/", json={
        "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=headers)
    eval_id = create.json()["id"]

    # prioritized -> financial_analysis (skipping stages)
    resp = await client.post(f"/evaluations/{eval_id}/transition", json={
        "to_stage": "financial_analysis",
    }, headers=headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_full_pipeline_traversal(client):
    """Walk through all 12 stages forward."""
    token, charity_id, cycle_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/evaluations/", json={
        "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=headers)
    eval_id = create.json()["id"]

    for i in range(1, len(STAGE_ORDER)):
        next_stage = STAGE_ORDER[i].value
        resp = await client.post(f"/evaluations/{eval_id}/transition", json={
            "to_stage": next_stage,
        }, headers=headers)
        assert resp.status_code == 200, f"Failed transitioning to {next_stage}: {resp.json()}"
        assert resp.json()["stage"] == next_stage

    assert resp.json()["stage"] == "published"


@pytest.mark.asyncio
async def test_stage_history(client):
    token, charity_id, cycle_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/evaluations/", json={
        "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=headers)
    eval_id = create.json()["id"]

    await client.post(f"/evaluations/{eval_id}/transition", json={
        "to_stage": "assigned", "note": "First transition",
    }, headers=headers)
    await client.post(f"/evaluations/{eval_id}/transition", json={
        "to_stage": "financials_acquisition",
    }, headers=headers)

    resp = await client.get(f"/evaluations/{eval_id}/history", headers=headers)
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) == 2
    assert history[0]["from_stage"] == "prioritized"
    assert history[0]["to_stage"] == "assigned"
    assert history[0]["note"] == "First transition"


@pytest.mark.asyncio
async def test_kanban_board(client):
    token, charity_id, cycle_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/evaluations/", json={
        "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=headers)
    eval_id = create.json()["id"]
    await client.post(f"/evaluations/{eval_id}/transition", json={
        "to_stage": "assigned",
    }, headers=headers)

    resp = await client.get(f"/evaluations/cycle/{cycle_id}/kanban", headers=headers)
    assert resp.status_code == 200
    columns = resp.json()
    assert len(columns) == 12  # All 12 stages
    assigned_col = next(c for c in columns if c["stage"] == "assigned")
    assert assigned_col["count"] == 1


@pytest.mark.asyncio
async def test_invalid_stage_name(client):
    token, charity_id, cycle_id = await _setup(client)
    headers = _auth(token)
    create = await client.post("/evaluations/", json={
        "charity_id": charity_id, "cycle_id": cycle_id,
    }, headers=headers)
    eval_id = create.json()["id"]
    resp = await client.post(f"/evaluations/{eval_id}/transition", json={
        "to_stage": "nonexistent_stage",
    }, headers=headers)
    assert resp.status_code == 400
