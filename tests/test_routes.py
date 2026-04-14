from uuid import UUID


def test_health_route(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_user_and_get_user(client):
    payload = {"username": "alice", "email": "alice@example.com"}
    create_response = client.post("/api/users", json=payload)
    assert create_response.status_code == 201
    user = create_response.json()

    assert UUID(user["id"])
    assert user["username"] == payload["username"]
    assert user["email"] == payload["email"]
    assert "created_at" in user

    get_response = client.get(f"/api/users/{user['id']}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["id"] == user["id"]
    assert fetched["username"] == payload["username"]
    assert fetched["email"] == payload["email"]


def test_create_user_conflict_on_username_or_email(client):
    first = {"username": "bob", "email": "bob@example.com"}
    assert client.post("/api/users", json=first).status_code == 201

    duplicate_username = {"username": "bob", "email": "bob2@example.com"}
    duplicate_email = {"username": "bob2", "email": "bob@example.com"}

    response_1 = client.post("/api/users", json=duplicate_username)
    response_2 = client.post("/api/users", json=duplicate_email)

    assert response_1.status_code == 409
    assert response_2.status_code == 409


def test_list_users(client):
    assert client.post("/api/users", json={"username": "user1", "email": "u1@example.com"}).status_code == 201
    assert client.post("/api/users", json={"username": "user2", "email": "u2@example.com"}).status_code == 201

    response = client.get("/api/users")
    assert response.status_code == 200

    users = response.json()
    usernames = {entry["username"] for entry in users}
    assert usernames == {"user1", "user2"}


def test_user_not_found_routes(client):
    missing_id = "00000000-0000-0000-0000-000000000000"

    assert client.get(f"/api/users/{missing_id}").status_code == 404
    assert client.get(f"/api/users/{missing_id}/attributes").status_code == 404
    assert client.put(f"/api/users/{missing_id}/attributes", json={"attributes": ["a"]}).status_code == 404
    assert client.get(f"/api/users/{missing_id}/group").status_code == 404


def test_run_grouping_uses_default_min_match_when_not_provided(client):
    response = client.post("/api/grouping/run")
    assert response.status_code == 200

    payload = response.json()
    assert payload["assigned_users"] == 0
    assert payload["min_match"] == 2


def test_run_grouping_rejects_negative_min_match(client):
    response = client.post("/api/grouping/run?min_match=-1")
    assert response.status_code == 422


def test_set_and_get_user_attributes(client):
    user_id = client.post(
        "/api/users",
        json={"username": "attrs", "email": "attrs@example.com"},
    ).json()["id"]

    set_response = client.put(
        f"/api/users/{user_id}/attributes",
        json={"attributes": [" Software ", "Engineer", "engineer", ""]},
    )
    assert set_response.status_code == 200
    assert set(set_response.json()["attributes"]) == {"software", "engineer"}

    get_response = client.get(f"/api/users/{user_id}/attributes")
    assert get_response.status_code == 200
    assert get_response.json()["attributes"] == ["engineer", "software"]


def test_grouping_workflow_via_routes(client):
    user_1 = client.post("/api/users", json={"username": "grp1", "email": "g1@example.com"}).json()["id"]
    user_2 = client.post("/api/users", json={"username": "grp2", "email": "g2@example.com"}).json()["id"]
    user_3 = client.post("/api/users", json={"username": "grp3", "email": "g3@example.com"}).json()["id"]

    assert client.put(
        f"/api/users/{user_1}/attributes",
        json={"attributes": ["software", "engineer", "senior"]},
    ).status_code == 200
    assert client.put(
        f"/api/users/{user_2}/attributes",
        json={"attributes": ["software", "engineer", "gamer"]},
    ).status_code == 200
    assert client.put(
        f"/api/users/{user_3}/attributes",
        json={"attributes": ["researcher", "counterstrike"]},
    ).status_code == 200

    before = client.get(f"/api/users/{user_1}/group")
    assert before.status_code == 200
    assert before.json()["group"] is None

    run_response = client.post("/api/grouping/run?min_match=2")
    assert run_response.status_code == 200
    assert run_response.json()["assigned_users"] == 3
    assert run_response.json()["min_match"] == 2

    group_1 = client.get(f"/api/users/{user_1}/group").json()["group"]
    group_2 = client.get(f"/api/users/{user_2}/group").json()["group"]
    group_3 = client.get(f"/api/users/{user_3}/group").json()["group"]

    assert group_1 is not None
    assert group_2 is not None
    assert group_3 is not None
    assert group_1["id"] == group_2["id"]
    assert group_3["id"] != group_1["id"]

    member_ids = {member["id"] for member in group_1["members"]}
    assert member_ids == {user_1, user_2}


def test_updating_attributes_removes_old_membership_until_next_batch(client):
    user_1 = client.post("/api/users", json={"username": "reg1", "email": "r1@example.com"}).json()["id"]
    user_2 = client.post("/api/users", json={"username": "reg2", "email": "r2@example.com"}).json()["id"]

    client.put(f"/api/users/{user_1}/attributes", json={"attributes": ["a", "b", "c"]})
    client.put(f"/api/users/{user_2}/attributes", json={"attributes": ["a", "b", "d"]})

    assert client.post("/api/grouping/run?min_match=2").status_code == 200
    initial_group = client.get(f"/api/users/{user_1}/group").json()["group"]
    assert initial_group is not None

    update = client.put(f"/api/users/{user_1}/attributes", json={"attributes": ["x", "y"]})
    assert update.status_code == 200

    interim_group = client.get(f"/api/users/{user_1}/group").json()["group"]
    assert interim_group is None

    rerun = client.post("/api/grouping/run?min_match=2")
    assert rerun.status_code == 200

    final_group = client.get(f"/api/users/{user_1}/group").json()["group"]
    assert final_group is not None
    assert final_group["id"] != initial_group["id"]
