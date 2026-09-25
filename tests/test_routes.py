import json,re
from datetime import timedelta
import pytest
from uairotas.validation import today

def map_payload(response):
    return json.loads(re.search(r'<script id="operational-map-data" type="application/json">(.*?)</script>', response.text, re.S).group(1))

@pytest.mark.parametrize("url",["/","/rotas","/frota","/relatorios","/relatorios/frota","/relatorios/rotas","/usuarios","/perfil","/alertas","/ordens/1"])
def test_private_pages_require_login(client,url):
    assert client.get(url).status_code==302

def test_filters_apply_to_orders_routes_and_map(authenticated,demo):
    data=map_payload(authenticated.get("/rotas?colaborador=2&status=route"))
    assert len(data["routes"])==1 and data["routes"][0]["driver_id"]==2
    assert len(data["orders"])==1 and data["orders"][0]["status"]=="A caminho"
    assert data["vehicles"]==[] and data["routes"][0]["path_kind"]=="planned"
    route_id=data["routes"][0]["id"]
    assert data["orders"][0]["route_id"]==route_id

def test_date_filter_and_empty_state(app,authenticated,demo):
    with app.app_context(): previous=today()-timedelta(days=1)
    a=map_payload(authenticated.get("/rotas"))
    b=map_payload(authenticated.get("/rotas",query_string={"data":previous.isoformat()}))
    assert {o["id"] for o in a["orders"]}.isdisjoint({o["id"] for o in b["orders"]})
    assert all(o["status"]=="Concluída" for o in b["orders"])
    empty=map_payload(authenticated.get("/rotas?data=2001-01-01"))
    assert empty["routes"]==[] and empty["orders"]==[]

@pytest.mark.parametrize("query",["data=bad","colaborador=999","colaborador=x","status=invalid"])
def test_invalid_filters_return_friendly_400(authenticated,query):
    response=authenticated.get("/rotas?"+query)
    assert response.status_code==400 and b"Confira" in response.data

def test_order_details_match_real_record(authenticated,demo):
    response=authenticated.get("/ordens/1")
    assert response.status_code==200 and b"DEMO-1-00-1" in response.data
    assert b"Cliente demonstrativo A" in response.data and "Instalação de fibra".encode() in response.data
    assert authenticated.get("/ordens/99999").status_code==404
