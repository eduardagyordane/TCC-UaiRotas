from pathlib import Path


def login(client):
    return client.post(
        "/login",
        data={"email": "admin@example.invalid", "password": "senha-de-teste-sem-segredo"},
    )


def test_home_exposes_mapbox_payload(client):
    login(client)
    response = client.get("/")

    assert response.status_code == 200
    assert b'id="home-mapbox-map"' in response.data
    assert b'data-map-source="home-map-data"' in response.data
    assert b'pk.test-mapbox-token' in response.data
    assert b'Escrit\xc3\xb3rio Uai Telecom' in response.data


def test_routes_exposes_routes_vehicles_orders_and_places(client):
    login(client)
    response = client.get("/rotas?colaborador=ana")

    assert b'data-selected-route="ana"' in response.data
    assert b'"routes"' in response.data
    assert b'"vehicles"' in response.data
    assert b'"orders"' in response.data
    assert b'"places"' in response.data
    assert b'"lat"' in response.data
    assert b'"lng"' in response.data


def test_mapbox_loader_builds_map_layers_markers_and_fallback():
    base = Path("uairotas/templates/base.html").read_text(encoding="utf-8")
    script = Path("uairotas/static/js/maps.js").read_text(encoding="utf-8")

    assert "https://api.mapbox.com/mapbox-gl-js/v3.30.0/mapbox-gl.js" in base
    assert "https://api.mapbox.com/mapbox-gl-js/v3.30.0/mapbox-gl.css" in base
    assert "new mapboxgl.Map" in script
    assert "map.addSource" in script
    assert "map.addLayer" in script
    assert "new mapboxgl.Marker" in script
    assert "https://api.mapbox.com/directions/v5/mapbox/driving/" in script
    assert 'element.dataset.routeApiStatus' in script
    assert 'type: "Feature"' in script
    assert 'geometry: matched.geometry' in script
    assert "MAPBOX_ACCESS_TOKEN" in script


def test_mapbox_token_is_loaded_from_environment_only():
    config = Path("uairotas/config.py").read_text(encoding="utf-8")
    env_example = Path(".env.example").read_text(encoding="utf-8")

    assert 'os.getenv("MAPBOX_ACCESS_TOKEN", "")' in config
    assert "MAPBOX_ACCESS_TOKEN=insira_seu_token_publico_restrito_aqui" in env_example
