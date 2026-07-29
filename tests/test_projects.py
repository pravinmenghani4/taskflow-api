"""End-to-end tests for the project API."""


def test_create_and_get_project(client):
    r = client.post("/projects", json={"title": "Alpha"})
    assert r.status_code == 201
    created = r.json()
    assert created["title"] == "Alpha"
    assert created["description"] is None

    project_id = created["id"]
    r = client.get(f"/projects/{project_id}")
    assert r.status_code == 200
    assert r.json()["id"] == project_id


def test_list_projects(client):
    client.post("/projects", json={"title": "One"})
    client.post("/projects", json={"title": "Two"})
    r = client.get("/projects")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_update_project(client):
    project_id = client.post("/projects", json={"title": "Draft"}).json()["id"]
    r = client.patch(
        f"/projects/{project_id}",
        json={"title": "Renamed", "description": "Updated scope"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Renamed"
    assert body["description"] == "Updated scope"


def test_delete_project(client):
    project_id = client.post("/projects", json={"title": "Temp"}).json()["id"]
    assert client.delete(f"/projects/{project_id}").status_code == 204
    assert client.get(f"/projects/{project_id}").status_code == 404


def test_project_validation_error(client):
    r = client.post("/projects", json={"title": ""})
    assert r.status_code == 422
