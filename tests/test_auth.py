def test_login_page_loads(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert b"Bem-vinda ao UaiRotas" in response.data
    assert b">Entrar<" in response.data


def test_private_home_redirects_to_login(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_valid_login_redirects_to_home(client):
    response = client.post(
        "/login",
        data={"email": "ADMIN@EXAMPLE.INVALID", "password": "senha-de-teste-sem-segredo"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Admin UaiRotas" in response.data
    assert b"Vis" in response.data
    assert b"Equipes em campo" in response.data


def test_invalid_login_displays_generic_error(client):
    response = client.post(
        "/login",
        data={"email": "admin@example.invalid", "password": "senha-incorreta"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"E-mail ou senha inv" in response.data


def test_authenticated_user_cannot_reopen_login(client):
    client.post(
        "/login",
        data={"email": "admin@example.invalid", "password": "senha-de-teste-sem-segredo"},
    )

    response = client.get("/login", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_logout_ends_session(client):
    client.post(
        "/login",
        data={"email": "admin@example.invalid", "password": "senha-de-teste-sem-segredo"},
    )

    response = client.post("/logout", follow_redirects=True)

    assert response.status_code == 200
    assert b"Sess" in response.data
    protected_response = client.get("/", follow_redirects=False)
    assert protected_response.status_code == 302


def test_external_next_url_is_rejected(client):
    response = client.post(
        "/login?next=https://example.com/phishing",
        data={"email": "admin@example.invalid", "password": "senha-de-teste-sem-segredo"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
