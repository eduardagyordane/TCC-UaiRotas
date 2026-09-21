import pytest


def login(client):
    return client.post(
        "/login",
        data={"email": "admin@uairotas.com", "password": "SenhaSegura123!"},
    )


@pytest.mark.parametrize("path", ["/relatorios", "/relatorios/frota", "/relatorios/rotas"])
def test_report_pages_require_authentication(client, path):
    response = client.get(path, follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_reports_overview_renders_summary_and_charts(client):
    login(client)
    response = client.get("/relatorios")
    assert response.status_code == 200
    assert "Resumo dos indicadores de rotas".encode() in response.data
    assert "Ordens concluídas".encode() in response.data
    assert b"4.826 km" in response.data
    assert b"R$ 12.116,70" in response.data
    assert "Evolução operacional".encode() in response.data
    assert "Situação das ordens".encode() in response.data
    assert b"report-donut--orders" in response.data


def test_reports_overview_links_to_detailed_reports(client):
    login(client)
    response = client.get("/relatorios")
    assert b'href="/relatorios/rotas?periodo=30dias"' in response.data
    assert b'href="/relatorios/frota?periodo=30dias"' in response.data
    assert "Relatório de rotas".encode() in response.data
    assert "Relatório de frota".encode() in response.data


def test_fleet_report_renders_costs_fuel_and_vehicle_details(client):
    login(client)
    response = client.get("/relatorios/frota")
    assert response.status_code == 200
    assert "Composição dos custos".encode() in response.data
    assert "Preço médio da gasolina".encode() in response.data
    assert "Desempenho por veículo".encode() in response.data
    assert b"QWE-4J21" in response.data
    assert b"RTY-8A13" in response.data
    assert b"R$ 8.420,30" in response.data
    assert b"10,8 km/L" in response.data


def test_route_report_renders_productivity_times_and_alerts(client):
    login(client)
    response = client.get("/relatorios/rotas")
    assert response.status_code == 200
    assert "Produtividade por colaborador".encode() in response.data
    assert "Tempo médio em trânsito".encode() in response.data
    assert "Detalhamento por colaborador".encode() in response.data
    assert b"Carlos Mendes" in response.data
    assert b"Ana Paula" in response.data
    assert b"Marcos Silva" in response.data
    assert b"2h18" in response.data
    assert b"report-lunch-alert" in response.data


@pytest.mark.parametrize(
    ("path", "period", "label"),
    [
        ("/relatorios", "7dias", "Últimos 7 dias"),
        ("/relatorios/frota", "90dias", "Últimos 90 dias"),
        ("/relatorios/rotas", "ano", "Ano de 2026"),
    ],
)
def test_report_period_filter_keeps_selected_value(client, path, period, label):
    login(client)
    response = client.get(f"{path}?periodo={period}")
    assert response.status_code == 200
    assert f'<option value="{period}" selected>{label}</option>'.encode() in response.data


def test_invalid_report_period_falls_back_to_thirty_days(client):
    login(client)
    response = client.get("/relatorios?periodo=invalido")
    assert '<option value="30dias" selected>Últimos 30 dias</option>'.encode() in response.data


def test_main_navigation_links_to_reports(client):
    login(client)
    response = client.get("/")
    assert b'href="/relatorios"' in response.data
