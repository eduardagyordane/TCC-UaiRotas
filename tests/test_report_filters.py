import csv
from datetime import timedelta
from html import unescape
from io import StringIO
import re

from flask import template_rendered
import pytest
from sqlalchemy import func, inspect, text

from uairotas.analytics import report_data
from uairotas.extensions import db
from uairotas.migrations import migrate
from uairotas.models import FleetRecord, SchemaMigration, ServiceOrder, Trip, Vehicle
from uairotas.validation import today


def rendered(client, path, query=None):
    contexts = []
    def capture(sender, template, context, **extra):
        contexts.append(context)
    with template_rendered.connected_to(capture, client.application):
        response = client.get(path, query_string=query)
    return response, contexts[-1] if contexts else None


def test_report_pages_have_distinct_content(authenticated, demo):
    summary = authenticated.get("/relatorios").text
    fleet = authenticated.get("/relatorios/frota").text
    routes = authenticated.get("/relatorios/rotas").text
    assert "Principais gastos da frota" in summary and "Visão geral dos atendimentos" in summary
    assert "Distribuição do tempo por motorista" not in summary
    assert "Preço médio da gasolina" not in summary and "Lançamentos da frota" not in summary
    assert "Manutenções no período" in fleet and "Composição dos custos" in fleet
    assert "OS concluídas" not in fleet and "Situação das ordens" not in fleet
    assert "Custos realizados" not in routes and "Custo por km" not in routes and "R$" not in routes
    assert "Produtividade por motorista" in routes and "Distribuição do tempo por motorista" in routes
    assert "Ocorrências das rotas no período" in routes
    for page in (summary, fleet, routes):
        assert 'name="veiculo"' in page and 'name="motorista"' in page and 'name="periodo"' in page


@pytest.mark.parametrize("vehicle_id,driver_id", [(1,None),(None,2),(3,3),(1,2)])
def test_filters_restrict_all_aggregates_and_detail_rows(app, authenticated, demo, vehicle_id, driver_id):
    query = {"periodo":"7dias"}
    if vehicle_id: query["veiculo"] = vehicle_id
    if driver_id: query["motorista"] = driver_id
    with app.app_context():
        end = today(); start = end - timedelta(days=6)
        orders = ServiceOrder.query.filter(ServiceOrder.date.between(start,end))
        trips = Trip.query.filter(Trip.date.between(start,end))
        costs = FleetRecord.query.filter(FleetRecord.date.between(start,end), FleetRecord.status=="posted")
        for field, value in (("vehicle_id", vehicle_id), ("driver_id", driver_id)):
            if value:
                orders=orders.filter_by(**{field:value});trips=trips.filter_by(**{field:value});costs=costs.filter_by(**{field:value})
        expected_complete = orders.filter_by(status="done").count()
        expected_cost = sum(record.amount_cents for record in costs)
        expected_distance = sum(trip.distance_m for trip in trips)
        expected_lunch = trips.filter(Trip.lunch_minutes>120).count()
    for path in ("/relatorios", "/relatorios/frota", "/relatorios/rotas"):
        response, context = rendered(authenticated,path,query)
        assert response.status_code==200
        data=context["overview"]
        assert data["total_cents"]==expected_cost
        assert data["complete"]==expected_complete
        assert data["distance_m"]==expected_distance
        assert data["lunch_excesses"]==expected_lunch
        assert sum(p["cents"] for p in data["series"])==expected_cost
        assert sum(p["orders"] for p in data["series"])==expected_complete
        assert sum(p["cents"] for p in data["costs"])==expected_cost
        if vehicle_id: assert all(row["vehicle"].id==vehicle_id for row in data["vehicles"])
        if driver_id: assert all(row["driver"].id==driver_id for row in data["drivers"])
        if context["records"]:
            assert all(not vehicle_id or r.vehicle_id==vehicle_id for r in context["records"].items)
            assert all(not driver_id or r.driver_id==driver_id for r in context["records"].items)


def test_filter_selection_persists_between_tabs_export_and_print(authenticated,demo):
    query={"periodo":"7dias","veiculo":2,"motorista":2}
    for path in ("/relatorios","/relatorios/frota","/relatorios/rotas"):
        response=authenticated.get(path,query_string=query)
        html=unescape(response.text)
        for endpoint in ("/relatorios?","/relatorios/frota?","/relatorios/rotas?"):
            assert endpoint+"periodo=7dias&veiculo=2&motorista=2" in html
        assert 'value="2" selected' in html
        assert "filter-selection" in html and "Colaborador Beta" in html and "DEM0002" in html
        export=re.search(r'href="([^"]*exportar.csv[^"]*)"',html).group(1)
        result=authenticated.get(export)
        assert result.status_code==200
        metadata=next(csv.reader(StringIO(result.data.decode("utf-8-sig")),delimiter=";"))
        assert metadata[-4:]==["Veículo","Equipe 2 · DEM0002","Motorista","Colaborador Beta"]


@pytest.mark.parametrize("query", [
    {"veiculo":"99999"},{"motorista":"99999"},{"veiculo":"-1"},{"motorista":"abc"},{"veiculo":"1 OR 1=1"},
])
def test_invalid_filter_is_rejected_in_html_and_csv(authenticated,demo,query):
    for path in ("/relatorios","/relatorios/frota","/relatorios/rotas","/relatorios/overview/exportar.csv",
                 "/relatorios/fleet/exportar.csv","/relatorios/routes/exportar.csv"):
        assert authenticated.get(path,query_string=query).status_code==400


def test_driver_reassignment_does_not_rewrite_historical_reports(app,demo):
    with app.app_context():
        end=today();start=end-timedelta(days=29)
        before=report_data(start,end,vehicle_id=1,driver_id=1)
        db.session.get(Vehicle,1).driver_id=2
        db.session.commit()
        after=report_data(start,end,vehicle_id=1,driver_id=1)
        for key in ("total_cents","complete","orders_total","distance_m","fuel_ml"):
            assert before[key]==after[key]
        assert after["total_cents"]>0 and after["complete"]>0


def test_unassigned_records_remain_in_all_but_not_named_filters(app,demo):
    with app.app_context():
        day=today()
        order=ServiceOrder(code="UNLINKED",date=day,time="15:00",customer="Sem vínculo",
                           address="Local de teste",service="Teste",driver_id=1,status="done",service_minutes=10)
        db.session.add_all([order,FleetRecord(kind="gasto",date=day,vehicle_id=1,amount_cents=98765)])
        db.session.commit()
        all_data=report_data(day,day)
        by_driver=report_data(day,day,driver_id=1)
        by_vehicle=report_data(day,day,vehicle_id=1)
        assert all_data["total_cents"]==98765 and by_driver["total_cents"]==0
        assert by_vehicle["total_cents"]==98765
        assert by_driver["complete"]==2 and by_vehicle["complete"]==1


def test_filtered_scheduled_maintenance_and_expense_pagination(app,authenticated,demo):
    with app.app_context():
        day=today()
        db.session.add_all([FleetRecord(kind="manutencao",date=day,vehicle_id=1,driver_id=1,amount_cents=9900,status="scheduled"),
                           FleetRecord(kind="manutencao",date=day,vehicle_id=2,driver_id=2,amount_cents=8800,status="scheduled")])
        db.session.add_all(FleetRecord(kind="gasto",date=day,vehicle_id=1,driver_id=1,amount_cents=100) for _ in range(30))
        db.session.commit()
    response,context=rendered(authenticated,"/relatorios/frota",{"veiculo":1,"motorista":1,"periodo":"7dias"})
    assert context["overview"]["scheduled_cents"]==9900 and context["overview"]["scheduled_maintenance"]==1
    assert len(context["records"].items)==25 and context["records"].has_next
    assert "pagina=2" in response.text and "motorista=1" in response.text
    _,other=rendered(authenticated,"/relatorios/frota",{"veiculo":1,"motorista":1,"periodo":"7dias","pagina":2})
    assert {r.id for r in context["records"].items}.isdisjoint(r.id for r in other["records"].items)


def test_csv_filtered_totals_match_their_module(app,authenticated,demo):
    query={"periodo":"7dias","veiculo":3,"motorista":3}
    _,context=rendered(authenticated,"/relatorios",query)
    data=context["overview"]
    csvs={}
    for module in ("overview","fleet","routes"):
        response=authenticated.get(f"/relatorios/{module}/exportar.csv",query_string=query)
        csvs[module]=list(csv.reader(StringIO(response.data.decode("utf-8-sig")),delimiter=";"))
    assert sum(int(row[2]) for row in csvs["overview"][2:])==data["total_cents"]
    assert sum(int(row[3]) for row in csvs["fleet"][2:])==data["total_cents"]
    assert sum(int(row[1]) for row in csvs["routes"][2:])==data["complete"]
    assert "Custo" not in csvs["routes"][1] and "OS concluídas" not in csvs["fleet"][1]


def test_migration_two_preserves_old_orders_without_guessing_real_links(app,demo):
    with app.app_context():
        day=today()
        db.session.add(ServiceOrder(code="LOCAL-OLD",date=day,time="16:00",customer="Preservado",
            address="Local de teste",service="Teste",driver_id=1,status="done",source="manual"))
        db.session.commit()
        count=ServiceOrder.query.count()
        # Reproduce the original schema without the new nullable column.
        db.session.execute(text("DELETE FROM schema_migrations WHERE version=2"))
        db.session.execute(text("""
            CREATE TABLE service_orders_legacy (
                id INTEGER NOT NULL PRIMARY KEY, code VARCHAR(40) NOT NULL UNIQUE,
                date DATE NOT NULL, time VARCHAR(5) NOT NULL, customer VARCHAR(120) NOT NULL,
                address VARCHAR(255) NOT NULL, service VARCHAR(120) NOT NULL,
                driver_id INTEGER NOT NULL REFERENCES drivers(id), status VARCHAR(20) NOT NULL,
                service_minutes INTEGER NOT NULL, lat FLOAT, lng FLOAT, source VARCHAR(20) NOT NULL
            )
        """))
        db.session.execute(text("""
            INSERT INTO service_orders_legacy
            SELECT id, code, date, time, customer, address, service, driver_id, status,
                   service_minutes, lat, lng, source FROM service_orders
        """))
        db.session.execute(text("DROP TABLE service_orders"))
        db.session.execute(text("ALTER TABLE service_orders_legacy RENAME TO service_orders"))
        db.session.execute(text("UPDATE fleet_records SET driver_id=NULL WHERE kind='combustivel'"))
        db.session.commit();db.session.expire_all()
        migrate();migrate()
        assert ServiceOrder.query.count()==count
        assert ServiceOrder.query.filter_by(code="LOCAL-OLD").one().vehicle_id is None
        assert ServiceOrder.query.filter_by(code="DEMO-1-00-1").one().vehicle_id==1
        assert all(r.driver_id==r.vehicle_id for r in FleetRecord.query.filter_by(kind="combustivel").all())
        assert db.session.get(SchemaMigration,2) is not None
        assert "vehicle_id" in {c["name"] for c in inspect(db.engine).get_columns("service_orders")}


def test_fuel_can_be_attributed_to_driver_in_create_and_edit(app,authenticated,demo):
    with app.app_context(): day=today().isoformat()
    data={"data":day,"veiculo":"1","motorista":"2","litros":"10","valor_litro":"6.00"}
    assert authenticated.post("/frota/registros/combustivel",data=data).status_code==302
    with app.app_context():
        record=FleetRecord.query.order_by(FleetRecord.id.desc()).first()
        record_id=record.id
        assert record.driver_id==2
    data["motorista"]="1"
    assert authenticated.post(f"/frota/cadastros/combustivel/{record_id}/editar",data=data).status_code==302
    with app.app_context():
        assert db.session.get(FleetRecord,record_id).driver_id==1
