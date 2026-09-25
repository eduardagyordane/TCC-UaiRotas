from datetime import timedelta
from io import BytesIO
import uuid
import pytest
from PIL import Image
from conftest import synthetic_cpf
from uairotas.extensions import db
from uairotas.main import fleet_values
from uairotas.models import AuditLog, Driver, FleetRecord, Vehicle
from uairotas.validation import today

def vehicle_data(**overrides):
    values=dict(placa_chassi="DEM-0001", apelido="Carro de teste", marca="Fiat", modelo="Strada", ano="2024",
                odometro="10000", grupo="Equipe", porte="Leve", tipo_mapa="Carro", tag="A1", hora_leitura="08:30")
    values.update(overrides);return values

def driver_data(**overrides):
    values=dict(nome="Motorista fictício", contato="(11) 99999-0001", cpf=synthetic_cpf(), cnh="90000000001",
                categoria="B", matricula="TESTE-1", identificador="Tag NFC", primeira_habilitacao="2009-01-01", validade="2030-01-01")
    values.update(overrides);return values

@pytest.fixture()
def fleet_base(app, authenticated):
    assert authenticated.post("/frota/registros/motorista", data=driver_data()).status_code == 302
    assert authenticated.post("/frota/registros/veiculo", data=vehicle_data(motorista="1")).status_code == 302

def payload(app, kind, **overrides):
    with app.app_context(): day=today()
    values=dict(veiculo="1", motorista="1", data=day.isoformat(), ultima_troca=day.isoformat(),
                proxima_troca=(day+timedelta(days=180)).isoformat(), quilometragem="10000", proxima_quilometragem="15000",
                valor="349.90", litros="40.125", valor_litro="6.19", tipo="Teste", descricao="Descrição de teste",
                observacoes="Agendamento de teste", posto="Posto de teste", submission_key=str(uuid.uuid4()))
    values.update(overrides);return values

def test_vehicle_and_driver_are_persisted_with_links(app, authenticated, fleet_base):
    with app.app_context():
        v=Vehicle.query.one();d=Driver.query.one()
        assert v.driver_id == d.id and v.plate == "DEM0001" and v.odometer == 10000
        assert d.phone == "11999990001" and d.cpf == synthetic_cpf()
        assert v.reading_time.hour == 8 and d.first_license.year == 2009
        assert AuditLog.query.count() == 2

@pytest.mark.parametrize("kind", ["oleo","combustivel","multa","gasto","manutencao"])
def test_each_financial_record_persists(app, authenticated, fleet_base, kind):
    data=payload(app,kind)
    response=authenticated.post("/frota/registros/"+kind,data=data)
    assert response.status_code == 302
    with app.app_context():
        record=FleetRecord.query.one()
        assert record.kind == kind
        assert record.amount_cents == (24837 if kind == "combustivel" else 34990)
        if kind == "combustivel": assert record.fuel_ml == 40125 and record.price_cents == 619
        if kind == "oleo": assert record.next_odometer == 15000
        if kind == "multa": assert record.driver_id == 1
        assert record.status == ("scheduled" if kind == "manutencao" else "posted")

@pytest.mark.parametrize("field,value", [("litros","-1"),("litros","NaN"),("litros","Infinity"),("litros","1.0001"),
    ("valor_litro","0"),("valor_litro","6.199"),("veiculo","9999"),("quilometragem","9999"),("data","2999-01-01")])
def test_bad_fuel_is_rejected_without_partial_writes(app, authenticated, fleet_base, field, value):
    response=authenticated.post("/frota/registros/combustivel",data=payload(app,"combustivel",**{field:value}))
    assert response.status_code == 422
    assert b'value="Posto de teste"' in response.data and b"data-auto-open" in response.data
    with app.app_context():
        assert FleetRecord.query.count() == 0 and Vehicle.query.one().odometer == 10000

@pytest.mark.parametrize("kind,overrides", [("veiculo",{"placa_chassi":"invalida"}),("veiculo",{"motorista":"999"}),
    ("veiculo",{"ano":"3000"}),("motorista",{"cpf":"11111111111"}),("motorista",{"contato":"abc"}),
    ("motorista",{"cnh":"x"}),("motorista",{"validade":"2000-01-01"})])
def test_invalid_vehicle_driver(app, authenticated, kind, overrides):
    data=vehicle_data(**overrides) if kind=="veiculo" else driver_data(**overrides)
    assert authenticated.post("/frota/registros/"+kind,data=data).status_code == 422
    with app.app_context(): assert Vehicle.query.count()+Driver.query.count()==0

def test_idempotency_and_actual_maintenance_cost(app, authenticated, fleet_base):
    data=payload(app,"manutencao",data="2030-01-01")
    for _ in range(2): assert authenticated.post("/frota/registros/manutencao",data=data).status_code==302
    with app.app_context():
        assert FleetRecord.query.count()==1
        day=today().isoformat()
    assert authenticated.post("/frota/manutencoes/1/concluir",data={"data":day,"valor":"290.12"}).status_code==302
    assert authenticated.post("/frota/manutencoes/1/concluir",data={"data":day,"valor":"290.12"}).status_code==400
    with app.app_context():
        record=FleetRecord.query.one()
        assert record.status=="posted" and record.amount_cents==29012 and record.date.isoformat()==day

def test_oil_dates_and_future_mileage(app, authenticated, fleet_base):
    data=payload(app,"oleo",proxima_troca="2000-01-01",proxima_quilometragem="9999")
    assert authenticated.post("/frota/registros/oleo",data=data).status_code==422
    with app.app_context(): assert FleetRecord.query.count()==0

def test_odometer_history_is_chronological(app, authenticated, fleet_base):
    with app.app_context(): day=today()
    data=payload(app,"oleo",ultima_troca=(day-timedelta(days=5)).isoformat(),quilometragem="11000")
    assert authenticated.post("/frota/registros/oleo",data=data).status_code==422
    data.update(quilometragem="9000")
    assert authenticated.post("/frota/registros/oleo",data=data).status_code==302
    with app.app_context(): assert Vehicle.query.one().odometer == 10000

def test_edits_persist_and_audit_without_corrupting_historical_readings(app, authenticated, fleet_base):
    assert authenticated.post("/frota/cadastros/veiculo/1/editar",data=vehicle_data(apelido="Editado",motorista="1")).status_code==302
    assert authenticated.post("/frota/cadastros/motorista/1/editar",data=driver_data(nome="Nome editado")).status_code==302
    data=payload(app,"oleo")
    assert authenticated.post("/frota/registros/oleo",data=data).status_code==302
    data["valor"]="399.01"
    assert authenticated.post("/frota/cadastros/oleo/1/editar",data=data).status_code==302
    data["quilometragem"]="11000"
    assert authenticated.post("/frota/cadastros/oleo/1/editar",data=data).status_code==422
    with app.app_context():
        assert Vehicle.query.one().nickname=="Editado" and Driver.query.one().name=="Nome editado"
        assert FleetRecord.query.one().amount_cents==39901 and FleetRecord.query.one().odometer==10000
        assert AuditLog.query.filter_by(action="update").count()==3
        assert fleet_values("veiculo",Vehicle.query.one())["placa_chassi"]=="DEM0001"
    assert "Nome editado".encode() in authenticated.get("/frota").data

def test_photo_decoded_resized_and_invalid_content_rejected(app, authenticated):
    image=BytesIO();Image.new("RGB",(640,320)).save(image,format="PNG");image.seek(0)
    data=driver_data();data["foto"]=(image,"foto.png")
    assert authenticated.post("/frota/registros/motorista",data=data).status_code==302
    response=authenticated.get("/motoristas/1/foto")
    assert response.mimetype=="image/jpeg"
    assert Image.open(BytesIO(response.data)).size==(256,128)
    data=driver_data(cpf=synthetic_cpf(900000002),cnh="90000000002")
    data["foto"]=(BytesIO(b"not an image"),"fake.png")
    assert authenticated.post("/frota/registros/motorista",data=data).status_code==422
    with app.app_context(): assert Driver.query.count()==1

def test_unknown_kind_and_missing_record(authenticated):
    assert authenticated.post("/frota/registros/unknown").status_code==404
    assert authenticated.get("/frota/cadastros/veiculo/99/editar").status_code==404
