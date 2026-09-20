from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_root_serves_index_html():
    response=client.get("/")
    assert response.status_code==200 and "cloudscope frontend" in response.text
def test_client_side_route_falls_back_to_index_html():
    response=client.get("/projects/42/analyses/7")
    assert response.status_code==200 and "cloudscope frontend" in response.text
def test_static_asset_is_served():
    response=client.get("/assets/app.js")
    assert response.status_code==200 and "cloudscope" in response.text
def test_unknown_api_route_returns_json_404_not_index_html():
    response=client.get("/api/does-not-exist")
    assert response.status_code==404
    assert response.headers["content-type"].startswith("application/json")
    assert "cloudscope frontend" not in response.text
def test_bare_api_path_returns_404():
    response=client.get("/api")
    assert response.status_code==404
def test_path_traversal_on_static_assets_is_blocked():
    response=client.get("/assets/..%2f..%2fapp/main.py")
    assert response.status_code in (400,403,404)
    assert "SECRET" not in response.text and "import" not in response.text
