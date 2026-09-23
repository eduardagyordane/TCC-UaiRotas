import pytest


def login(client):
    return client.post(
        "/login",
        data={"email": "admin@example.invalid", "password": "senha-de-teste-sem-segredo"},
    )


def test_fleet_requires_authentication(client):
    response = client.get("/frota", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_fleet_page_renders_summary_vehicles_and_costs(client):
    login(client)
    response = client.get("/frota")

    assert response.status_code == 200
    assert b"Ve\xc3\xadculos cadastrados" in response.data
    assert b"T\xc3\xa9cnicos vinculados" in response.data
    assert b"4.826 km" in response.data
    assert b"R$ 6,19" in response.data
    assert b"Locais de interesse" in response.data
    assert b"DEM-0001" in response.data
    assert "Custos do mês".encode() in response.data


def test_fleet_page_shows_oil_and_maintenance_information(client):
    login(client)
    response = client.get("/frota")

    assert b"\xc3\x9altima troca de \xc3\xb3leo" in response.data
    assert b"Vence em 220 km" in response.data
    assert b"Pr\xc3\xb3ximas manuten\xc3\xa7\xc3\xb5es" in response.data
    assert b"Revis\xc3\xa3o preventiva" in response.data


def test_fleet_contains_all_creation_dialogs_and_fields(client):
    login(client)
    response = client.get("/frota")

    for dialog_id in (
        b"vehicle-dialog",
        b"driver-dialog",
        b"oil-dialog",
        b"fuel-dialog",
        b"fine-dialog",
        b"expense-dialog",
        b"maintenance-dialog",
    ):
        assert dialog_id in response.data

    for field_name in (
        b' name="placa_chassi"',
        b' name="cpf"',
        b' name="ultima_troca"',
        b' name="valor_litro"',
        b' name="motorista"',
        b' name="descricao"',
        b' name="observacoes"',
    ):
        assert field_name in response.data


@pytest.mark.parametrize(
    ("record_type", "payload", "success_message"),
    [
        ("veiculo", {"placa_chassi": "VEICULO-FICTICIO", "apelido": "Carro 05", "marca": "Fiat", "modelo": "Strada", "odometro": "10000"}, "Veículo registrado com sucesso."),
        ("motorista", {"nome": "Motorista Fictício", "contato": "CONTATO-FICTICIO", "cpf": "CPF-FICTICIO", "cnh": "CNH-FICTICIA"}, "Motorista registrado com sucesso."),
        ("oleo", {"veiculo": "VEICULO-FICTICIO", "ultima_troca": "2026-09-18", "proxima_troca": "2027-01-18", "quilometragem": "10000", "valor": "349.90"}, "Troca de óleo registrada com sucesso."),
        ("combustivel", {"data": "2026-09-18", "veiculo": "VEICULO-FICTICIO", "litros": "40", "valor_litro": "6.19"}, "Abastecimento registrado com sucesso."),
        ("multa", {"data": "2026-09-18", "veiculo": "VEICULO-FICTICIO", "motorista": "Motorista Fictício", "tipo": "Velocidade", "descricao": "Teste", "valor": "195.23"}, "Multa registrada com sucesso."),
        ("gasto", {"data": "2026-09-18", "tipo": "Pedágio", "descricao": "Viagem", "valor": "18.50"}, "Gasto registrado com sucesso."),
        ("manutencao", {"data": "2026-09-20", "veiculo": "VEICULO-FICTICIO", "tipo": "Revisão", "valor": "600"}, "Manutenção agendada com sucesso."),
    ],
)
def test_create_fleet_records(client, record_type, payload, success_message):
    login(client)
    response = client.post(
        f"/frota/registros/{record_type}",
        data=payload,
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert success_message.encode() in response.data


def test_create_fleet_record_validates_required_fields(client):
    login(client)
    response = client.post(
        "/frota/registros/veiculo",
        data={"placa_chassi": "VEICULO-FICTICIO"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Preencha todos os campos obrigatórios".encode() in response.data


def test_unknown_fleet_record_type_returns_404(client):
    login(client)
    response = client.post("/frota/registros/desconhecido", data={})

    assert response.status_code == 404


def test_home_navigation_links_to_fleet(client):
    login(client)
    response = client.get("/")

    assert b'href="/frota"' in response.data
