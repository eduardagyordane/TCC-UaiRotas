import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

def test_home_empty_uses_local_data(authenticated):
    response = authenticated.get("/")
    assert response.status_code == 200
    assert "Registros locais".encode() in response.data
    assert "Nenhuma ordem registrada".encode() in response.data
    assert b"Mapbox" not in response.data  # UI does not claim provider synchronization.

def test_home_demo_is_identified_and_links_orders(authenticated, demo):
    response = authenticated.get("/")
    assert "Dados demonstrativos".encode() in response.data
    assert "ainda não conectados".encode() in response.data
    assert b"DEMO-1-00-1" in response.data
    assert b"138 minutos" in response.data

def test_all_internal_links_and_dialog_labels_work(authenticated, demo):
    class Page(HTMLParser):
        def __init__(self):
            super().__init__(); self.links=[]; self.ids=set(); self.dialogs=[]
        def handle_starttag(self, tag, attrs):
            attrs=dict(attrs)
            if "id" in attrs: self.ids.add(attrs["id"])
            if tag == "a" and attrs.get("href","").startswith("/"): self.links.append(attrs["href"])
            if tag == "dialog": self.dialogs.append(attrs.get("aria-labelledby"))
    links=set()
    for path in ["/","/rotas","/frota","/relatorios","/relatorios/frota","/relatorios/rotas","/usuarios","/perfil","/alertas"]:
        response=authenticated.get(path)
        assert response.status_code == 200
        page=Page();page.feed(response.text)
        assert all(label in page.ids for label in page.dialogs)
        links.update(page.links)
    for url in links:
        assert authenticated.get(urlsplit(url)._replace(fragment="").geturl()).status_code == 200, url
