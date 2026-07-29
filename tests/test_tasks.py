"""End-to-end tests for the task API — the automated 'does it run correctly?' check."""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_and_get_task(client):
    r = client.post("/tasks", json={"title": "Write the PRD"})
    assert r.status_code == 201
    created = r.json()
    assert created["title"] == "Write the PRD"
    assert created["status"] == "todo"

    task_id = created["id"]
    r = client.get(f"/tasks/{task_id}")
    assert r.status_code == 200
    assert r.json()["id"] == task_id


def test_list_tasks(client):
    client.post("/tasks", json={"title": "A"})
    client.post("/tasks", json={"title": "B"})
    r = client.get("/tasks")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_update_task(client):
    task_id = client.post("/tasks", json={"title": "Draft"}).json()["id"]
    r = client.patch(f"/tasks/{task_id}", json={"status": "in_progress"})
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"


def test_delete_task(client):
    task_id = client.post("/tasks", json={"title": "Temp"}).json()["id"]
    assert client.delete(f"/tasks/{task_id}").status_code == 204
    assert client.get(f"/tasks/{task_id}").status_code == 404


def test_validation_error(client):
    # Empty title violates the schema's min_length=1 rule.
    r = client.post("/tasks", json={"title": ""})
    assert r.status_code == 422
