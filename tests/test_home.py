def login(client):
    return client.post(
        "/login",
        data={"email": "admin@uairotas.com", "password": "SenhaSegura123!"},
    )


def test_home_requires_authentication(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_home_renders_operational_summary(client):
    login(client)
    response = client.get("/")

    assert response.status_code == 200
    assert b"Ve" in response.data
    assert b"T" in response.data
    assert b"Ordens de servi" in response.data
    assert b"Alertas ativos" in response.data


def test_home_renders_service_orders(client):
    login(client)
    response = client.get("/")

    assert b"OS 10482" in response.data
    assert b"Marina Oliveira" in response.data
    assert b"Instala" in response.data
    assert b"Carlos Mendes" in response.data


def test_home_renders_lunch_alert(client):
    login(client)
    response = client.get("/")

    assert b"Almo" in response.data
    assert b"2h18" in response.data


def test_home_has_accessible_theme_and_navigation_controls(client):
    login(client)
    response = client.get("/")

    assert b'data-theme-toggle' in response.data
    assert b'aria-label="Ativar modo escuro"' in response.data
    assert b'aria-current="page"' in response.data
    assert b'data-nav-toggle' in response.data


def test_home_has_profile_logout_form(client):
    login(client)
    response = client.get("/")

    assert b'action="/logout"' in response.data
    assert b'name="csrf_token"' in response.data
