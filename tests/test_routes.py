def login(client):
    return client.post(
        "/login",
        data={"email": "admin@uairotas.com", "password": "SenhaSegura123!"},
    )


def test_routes_requires_authentication(client):
    response = client.get("/rotas", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_routes_page_renders_map_orders_and_collaborators(client):
    login(client)
    response = client.get("/rotas")

    assert response.status_code == 200
    assert b"Rotas e ordens de servi" in response.data
    assert b"data-interactive-map" in response.data
    assert b"Carlos Mendes" in response.data
    assert b"Ana Paula" in response.data
    assert b"Marcos Silva" in response.data
    assert b"OS 10482" in response.data


def test_routes_page_contains_ixc_order_details(client):
    login(client)
    response = client.get("/rotas")

    assert b"Marina Oliveira" in response.data
    assert b"Rua Major Gote" in response.data
    assert b"Instala" in response.data


def test_routes_page_contains_interest_places_and_lunch_alert(client):
    login(client)
    response = client.get("/rotas")

    assert b"Almoxarifado" in response.data
    assert b"Escrit" in response.data
    assert b"Posto" in response.data
    assert b"Almo" in response.data
    assert b"2h18" in response.data


def test_routes_filter_by_collaborator(client):
    login(client)
    response = client.get("/rotas?colaborador=ana")

    assert response.status_code == 200
    assert b"OS 10496" in response.data
    assert b"OS 10503" in response.data
    assert b"Marina Oliveira" not in response.data


def test_routes_filter_by_status(client):
    login(client)
    response = client.get("/rotas?status=late")

    assert response.status_code == 200
    assert b"OS 10511" in response.data
    assert b"Mercado S" not in response.data


def test_routes_empty_filter_result(client):
    login(client)
    response = client.get("/rotas?colaborador=carlos&status=late")

    assert response.status_code == 200
    assert b"Nenhuma ordem encontrada" in response.data


def test_home_navigation_links_to_routes(client):
    login(client)
    response = client.get("/")

    assert b'href="/rotas"' in response.data
