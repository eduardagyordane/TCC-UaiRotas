"""Explicit, fictitious seed data. Never called automatically by a web request."""
from datetime import timedelta

from .extensions import db
from .models import Driver, FleetRecord, Place, ServiceOrder, Trip, Vehicle
from .validation import fuel_total, today


def seed_demo():
    if any(db.session.query(model.id).first() for model in (Driver, Vehicle, Trip, ServiceOrder, Place, FleetRecord)):
        raise ValueError("Use uma base operacional vazia para inserir a demonstração.")
    day = today()
    paths = [
        [[-46.535, -18.6042], [-46.5272, -18.5934], [-46.5189, -18.5826], [-46.5078, -18.5718]],
        [[-46.4934, -18.5617], [-46.5061, -18.5702], [-46.521, -18.5786], [-46.537, -18.5888]],
        [[-46.5091, -18.5996], [-46.5054, -18.589], [-46.498, -18.5791], [-46.4862, -18.5684]],
    ]
    for i, name in enumerate(("Colaborador Alfa", "Colaborador Beta", "Colaborador Gama")):
        # Intentionally invalid document numbers, so demonstration records cannot
        # be mistaken for verified personal documents. Replace them before editing.
        driver = Driver(name=name, phone="CONTATO-DEMO-" + str(i + 1), cpf=str(i + 1) * 11,
                        license_number=str(i + 4) * 11, category="B", source="demo")
        vehicle = Vehicle(plate=f"DEM000{i + 1}", nickname=f"Equipe {i + 1}", brand=("Fiat", "Volkswagen", "Renault")[i],
                          model=("Strada", "Saveiro", "Oroch")[i], year=2023, odometer=(48320, 61780, 72405)[i],
                          reading_date=day, driver=driver, source="demo")
        db.session.add_all([driver, vehicle])
        db.session.flush()
        for offset in range(35):
            date = day - timedelta(days=offset)
            trip = Trip(date=date, vehicle=vehicle, driver=driver, distance_m=19200 + i * 7100 + (offset % 5) * 2400,
                        transit_minutes=70 + i * 10 + offset % 20,
                        lunch_minutes=138 if i == 2 and offset == 0 else 65 + i * 8,
                        deviations=1 if i == 2 and offset % 9 == 0 else 0, points=paths[i], source="demo")
            db.session.add(trip)
            for sequence in range(3):
                status = "done" if offset or sequence == 0 else ("progress", "route", "late")[i] if sequence == 1 else "scheduled"
                point = paths[i][sequence + 1]
                db.session.add(ServiceOrder(code=f"DEMO-{i+1}-{offset:02d}-{sequence+1}", date=date,
                    time=("08:30", "10:00", "13:30")[sequence], customer=f"Cliente demonstrativo {chr(65 + i * 3 + sequence)}",
                    address=f"Ponto demonstrativo {i * 3 + sequence + 1} — Patos de Minas",
                    service=("Instalação de fibra", "Manutenção de link", "Suporte técnico")[sequence],
                    driver=driver, vehicle=vehicle, status=status, service_minutes=40 + sequence * 15 if status == "done" else 0,
                    lng=point[0], lat=point[1], source="demo"))
        for offset in (1, 8, 15, 22, 29):
            db.session.add(FleetRecord(kind="combustivel", date=day-timedelta(days=offset), vehicle=vehicle, driver=driver,
                amount_cents=fuel_total(40500, 619-offset), fuel_ml=40500, price_cents=619-offset,
                description="Posto demonstrativo", source="demo"))
        db.session.add(FleetRecord(kind="oleo", date=day-timedelta(days=60), vehicle=vehicle, driver=driver, amount_cents=34990,
            odometer=vehicle.odometer-4000, next_date=day+timedelta(days=5 if i == 1 else 45),
            next_odometer=vehicle.odometer+(220 if i == 1 else 4000), source="demo"))
        if i == 2:
            db.session.add(FleetRecord(kind="manutencao", date=day+timedelta(days=2), vehicle=vehicle, driver=driver,
                amount_cents=68000, subtype="Revisão preventiva", status="scheduled", source="demo"))
        if i == 0:
            db.session.add(FleetRecord(kind="manutencao", date=day-timedelta(days=5), vehicle=vehicle, driver=driver,
                amount_cents=18000, subtype="Alinhamento", source="demo"))
        if i == 1:
            db.session.add(FleetRecord(kind="multa", date=day-timedelta(days=3), vehicle=vehicle, driver=driver,
                amount_cents=19523, subtype="Exemplo de infração", description="Ocorrência demonstrativa", source="demo"))
    db.session.add(FleetRecord(kind="gasto", date=day-timedelta(days=4), amount_cents=1850,
                              subtype="Material", description="Compra demonstrativa", source="demo"))
    for name, category, coordinates in [
        ("Base demonstrativa", "office", [-46.5181, -18.5789]),
        ("Depósito demonstrativo", "warehouse", [-46.532, -18.589]),
        ("Almoço demonstrativo", "restaurant", [-46.498, -18.5791]),
        ("Posto demonstrativo", "fuel", [-46.5078, -18.5718]),
    ]:
        db.session.add(Place(name=name, category=category, address="Endereço fictício para demonstração",
                            lng=coordinates[0], lat=coordinates[1], source="demo"))
    db.session.commit()
