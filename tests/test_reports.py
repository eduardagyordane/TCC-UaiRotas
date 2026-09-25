import csv
from datetime import timedelta
from io import StringIO
from sqlalchemy import func
from uairotas.analytics import period,report_data
from uairotas.extensions import db
from uairotas.models import FleetRecord,ServiceOrder,Trip,Vehicle
from uairotas.validation import today

def test_shared_totals_reconcile(app,demo):
    with app.app_context():
        end=today();start=end-timedelta(days=29);data=report_data(start,end)
        assert data["total_cents"]==sum(r["cents"] for r in data["costs"])
        assert data["total_cents"]==sum(r["cents"] for r in data["vehicles"])+data["unattributed_cents"]
        assert data["total_cents"]==sum(r["cents"] for r in data["series"])
        assert data["complete"]==sum(r["completed"] for r in data["drivers"])==sum(r["orders"] for r in data["series"])
        assert data["distance_m"]==sum(r["distance_m"] for r in data["vehicles"])==sum(r["distance_m"] for r in data["drivers"])
        assert all(r["order_height"]<=100 and r["cost_height"]<=100 for r in data["series"])
        assert data["fuel_points"] and all(p["cents"] <= data["fuel_axis"] for p in data["fuel_points"])

def test_period_boundaries_exclude_scheduled_and_future(app,demo):
    with app.test_request_context("/relatorios?periodo=7dias"):
        _,_,start,end=period()
        assert (end-start).days==6
        expected=db.session.query(func.sum(FleetRecord.amount_cents)).filter(FleetRecord.date.between(start,end),FleetRecord.status=="posted").scalar()
        db.session.add_all([
            FleetRecord(kind="gasto",date=start-timedelta(days=1),amount_cents=990000),
            FleetRecord(kind="gasto",date=end+timedelta(days=1),amount_cents=880000),
            FleetRecord(kind="manutencao",date=end,amount_cents=770000,status="scheduled")])
        db.session.commit()
        data=report_data(start,end)
        assert data["total_cents"]==expected and data["scheduled_cents"]==770000

def test_csv_uses_same_period_and_neutralizes_formulas(app,authenticated,demo):
    with app.app_context():
        vehicle=db.session.get(Vehicle,1);vehicle.nickname="=EXTERNAL()";db.session.commit()
        expected=report_data(today()-timedelta(days=6),today())["total_cents"]
    response=authenticated.get("/relatorios/fleet/exportar.csv?periodo=7dias")
    rows=list(csv.reader(StringIO(response.data.decode("utf-8-sig")),delimiter=";"))
    assert response.status_code==200 and sum(int(r[3]) for r in rows[2:])==expected
    assert any(row[0]=="'=EXTERNAL()" for row in rows)
    other=authenticated.get("/relatorios/fleet/exportar.csv?periodo=30dias")
    assert response.data!=other.data

def test_zero_distance_not_divided_and_period_retained(app,authenticated):
    with app.app_context():
        db.session.add(FleetRecord(kind="gasto",date=today(),amount_cents=120));db.session.commit()
        data=report_data(today(),today());assert data["cost_per_km"] is None
    response=authenticated.get("/relatorios?periodo=7dias")
    assert b"/relatorios/frota?periodo=7dias" in response.data
    assert b"/relatorios/rotas?periodo=7dias" in response.data
    assert b"0,0 km" in response.data
    fleet_response=authenticated.get("/relatorios/frota?periodo=7dias")
    assert b"Sem dist" in fleet_response.data and b"data-alternative" in fleet_response.data

def test_fuel_weighted_mean_and_time_components(app,demo):
    with app.app_context():
        day=today()
        db.session.add_all([FleetRecord(kind="combustivel",date=day,amount_cents=6000,price_cents=600,fuel_ml=10000),
                           FleetRecord(kind="combustivel",date=day,amount_cents=21000,price_cents=700,fuel_ml=30000)])
        db.session.commit()
        data=report_data(day,day)
        assert data["fuel_points"][0]["cents"]==675
        assert sum(row["times"]["service"] for row in data["drivers"])==120
        assert sum(row["times"]["lunch"] for row in data["drivers"])==65+73+138

def test_report_module_exports_and_period_fallback(authenticated,demo):
    for module in ("overview","fleet","routes"):
        assert authenticated.get(f"/relatorios/{module}/exportar.csv?periodo=ano").status_code==200
    assert authenticated.get("/relatorios/unknown/exportar.csv").status_code==404
    assert authenticated.get("/relatorios?periodo=bad").status_code==200
