from pathlib import Path
import pytest
from test_routes import map_payload

@pytest.mark.parametrize("path",["/frota","/relatorios","/relatorios/frota","/relatorios/rotas","/usuarios","/perfil","/alertas"])
def test_mapbox_assets_only_on_map_pages(authenticated,path):
    page=authenticated.get(path)
    assert b"mapbox-gl.js" not in page.data and b"mapbox-gl.css" not in page.data and b"js/maps.js" not in page.data

def test_login_has_no_mapbox_assets(client):
    assert b"mapbox-gl.js" not in client.get("/login").data

@pytest.mark.parametrize("path",["/","/rotas"])
def test_map_pages_have_complete_data_and_no_legacy_map(authenticated,demo,path):
    response=authenticated.get(path)
    assert b"mapbox-gl.js" in response.data and b'data-map-retry' in response.data
    payload=map_payload(response)
    assert payload["vehicles"]==[]
    assert len(payload["places"])==4 and len({p["type"] for p in payload["places"]})==4
    assert {"customer","address","service","status"} <= set(payload["orders"][0])
    assert b"city-map" not in response.data and b"legacy-map" not in response.data

def test_marker_motion_respects_mapbox_position_and_reduced_motion():
    css=Path("uairotas/static/css/refinements.css").read_text()
    assert ".map-alert-ring { animation:" in css and "@media (prefers-reduced-motion:reduce)" in css
    block=css.split(".map-marker {")[1].split("}")[0]
    assert "animation:" not in block and "transform:" not in block
