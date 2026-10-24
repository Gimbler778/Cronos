from fastapi.testclient import TestClient

from apps.api.main import app


def test_sample_api_flow():
    client = TestClient(app)
    assert client.post("/api/v1/sample-data").status_code == 200
    assert client.post("/api/v1/validate").json()["valid"] is True
    response = client.post("/api/v1/optimization-runs", json={"random_seed": 42, "population_size": 10, "max_generations": 10})
    assert response.status_code == 200
    run_id = response.json()["id"]
    assert client.get(f"/api/v1/optimization-runs/{run_id}/schedule").status_code == 200
    assert client.get(f"/api/v1/optimization-runs/{run_id}/metrics").status_code == 200
    assert client.get(f"/api/v1/optimization-runs/{run_id}/export.csv").text.startswith("session_id,slot_id,room_id")


def test_invalid_reference_is_rejected():
    client = TestClient(app)
    payload = {"teaching_requirements": [{"id": "bad", "course_id": "missing", "section_id": "missing", "faculty_id": "missing", "required_sessions": 1}]}
    response = client.put("/api/v1/data", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INVALID_INPUT"


def test_collection_crud_and_run_analytics():
    client = TestClient(app)
    client.post("/api/v1/sample-data")
    new_room = {"id": "r3", "name": "Room 3", "capacity": 50, "room_type": "lecture"}
    assert client.post("/api/v1/rooms", json=new_room).status_code == 201
    assert any(item["id"] == "r3" for item in client.get("/api/v1/rooms").json())
    assert client.put("/api/v1/rooms/r3", json={"name": "Room 3 Updated"}).status_code == 200
    assert client.delete("/api/v1/rooms/r3").status_code == 204
    run = client.post("/api/v1/optimization-runs", json={"random_seed": 9, "population_size": 8, "max_generations": 4}).json()
    assert client.get("/api/v1/optimization-runs").status_code == 200
    analytics = client.get(f"/api/v1/optimization-runs/{run['id']}/analytics")
    assert analytics.status_code == 200
    assert "sessions_by_slot" in analytics.json()


def test_request_bounds_and_baseline():
    client = TestClient(app)
    client.post("/api/v1/sample-data")
    invalid = client.post("/api/v1/optimization-runs", json={"population_size": 1})
    assert invalid.status_code == 422
    baseline = client.post("/api/v1/baseline", json={"random_seed": 42})
    assert baseline.status_code == 200
    assert {"status", "hard_violations", "soft_penalty"} <= baseline.json().keys()


def test_run_schedule_uses_input_snapshot():
    client = TestClient(app)
    client.post("/api/v1/sample-data")
    run = client.post("/api/v1/optimization-runs", json={"random_seed": 42, "population_size": 8, "max_generations": 4}).json()
    client.put("/api/v1/data", json={"faculty": [], "rooms": [], "sections": [], "courses": [], "time_slots": [], "teaching_requirements": []})
    schedule = client.get(f"/api/v1/optimization-runs/{run['id']}/schedule")
    assert schedule.status_code == 200
    assert len(schedule.json()["sessions"]) == 2
