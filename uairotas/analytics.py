"""Shared queries for Home, Fleet and Reports; all ranges are inclusive."""
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import and_, func
from flask import abort, request

from .extensions import db
from .models import AlertAcknowledgement, Driver, FleetRecord, Place, ServiceOrder, Trip, Vehicle
from .validation import Form, decimal_br, money, today

STATUS = {"scheduled": "Agendada", "route": "A caminho", "progress": "Em atendimento", "done": "Concluída", "late": "Atrasada"}
COLORS = ["#d9233f", "#2d78b7", "#b17a00", "#8259b0", "#27845c"]
COSTS = {"combustivel": "Combustível", "oleo": "Trocas de óleo", "manutencao": "Manutenções", "multa": "Multas", "gasto": "Outros gastos"}


def period():
    end = today()
    selected = request.args.get("periodo", "30dias")
    periods = {"7dias": "Últimos 7 dias", "30dias": "Últimos 30 dias", "90dias": "Últimos 90 dias", "ano": f"Ano de {end.year}"}
    if selected not in periods:
        selected = "30dias"
    start = end.replace(month=1, day=1) if selected == "ano" else end - timedelta(days={"7dias": 6, "30dias": 29, "90dias": 89}[selected])
    return selected, periods, start, end


def selected_date():
    value = Form({"date": request.args.get("data", today().isoformat())})
    day = value.date("date", "Data")
    if value.errors:
        abort(400)
    return day


def source_info():
    demo = any(db.session.query(model.id).filter_by(source="demo").first() is not None for model in (Vehicle, ServiceOrder, Trip, Place))
    return {"demo": demo, "label": "Dados demonstrativos" if demo else "Registros locais",
            "description": "Exemplos fictícios para testes." if demo else "Dados cadastrados neste sistema.",
            "integration": "Cobli e IXC ainda não conectados."}


def route_context(day, driver_id=None, status=None):
    trip_query = Trip.query.filter_by(date=day)
    order_query = ServiceOrder.query.filter_by(date=day)
    if driver_id:
        trip_query = trip_query.filter_by(driver_id=driver_id)
        order_query = order_query.filter_by(driver_id=driver_id)
    if status:
        order_query = order_query.filter_by(status=status)
        matching_drivers = db.select(ServiceOrder.driver_id).where(ServiceOrder.date == day, ServiceOrder.status == status)
        trip_query = trip_query.filter(Trip.driver_id.in_(matching_drivers))
    trips = trip_query.order_by(Trip.id).all()
    orders = order_query.order_by(ServiceOrder.time, ServiceOrder.id).all()
    places = Place.query.order_by(Place.name).all()
    colors = {driver.id: COLORS[i % len(COLORS)] for i, driver in enumerate(Driver.query.order_by(Driver.id).all())}
    routes = [{"id": str(trip.id), "driver_id": trip.driver_id, "name": trip.driver.name,
               "color": colors[trip.driver_id], "points": trip.points, "path_kind": trip.path_kind,
               "date": day.isoformat(), "demo": trip.source == "demo"} for trip in trips]
    route_for_driver = {trip.driver_id: str(trip.id) for trip in trips}
    map_orders = [{"id": str(order.id), "code": order.code, "name": order.customer, "customer": order.customer,
                   "address": order.address, "service": order.service, "status": STATUS[order.status],
                   "route_id": route_for_driver.get(order.driver_id), "label": str(i + 1),
                   "lat": order.lat, "lng": order.lng} for i, order in enumerate(orders) if order.lat is not None and order.lng is not None]
    payload = {"demo": any(trip.source == "demo" for trip in trips), "date": day.isoformat(),
               "center": {"lat": -18.5789, "lng": -46.5181}, "zoom": 13,
               "routes": routes, "vehicles": [], "orders": map_orders,
               "places": [{"id": str(p.id), "name": p.name, "address": p.address, "type": p.category,
                           "lat": p.lat, "lng": p.lng} for p in places]}
    # No invented current positions: a planned route's endpoint is not telemetry.
    return {"trips": trips, "orders": orders, "places": places, "map_data": payload, "colors": colors}


def report_filters():
    """Validate IDs once for both HTML and CSV; never infer current assignments."""
    form = Form(request.args)
    values = {}
    for key, label, model in (("veiculo", "Veículo", Vehicle), ("motorista", "Motorista", Driver)):
        raw = request.args.get(key, "todos")
        values[key] = None if raw in ("", "todos") else form.relation(key, label, model)
    if form.errors:
        abort(400)
    return values["veiculo"], values["motorista"]


def report_conditions(start, end, vehicle_id=None, driver_id=None):
    conditions = []
    for model in (FleetRecord, Trip, ServiceOrder):
        terms = [model.date.between(start, end)]
        if vehicle_id is not None:
            terms.append(model.vehicle_id == vehicle_id)
        if driver_id is not None:
            terms.append(model.driver_id == driver_id)
        conditions.append(and_(*terms))
    return tuple(conditions)


def report_data(start, end, vehicle_id=None, driver_id=None):
    record_filter, trip_filter, order_filter = report_conditions(start, end, vehicle_id, driver_id)
    records = FleetRecord.query.filter(record_filter, FleetRecord.status == "posted")
    total = records.with_entities(func.coalesce(func.sum(FleetRecord.amount_cents), 0)).scalar()
    distance = db.session.query(func.coalesce(func.sum(Trip.distance_m), 0)).filter(trip_filter).scalar()
    fuel_ml = records.with_entities(func.coalesce(func.sum(FleetRecord.fuel_ml), 0)).scalar()
    statuses = dict(db.session.query(ServiceOrder.status, func.count()).filter(order_filter).group_by(ServiceOrder.status).all())
    complete = statuses.get("done", 0)
    orders_total = sum(statuses.values())
    service_average = db.session.query(func.avg(ServiceOrder.service_minutes)).filter(order_filter, ServiceOrder.status == "done").scalar()
    costs = []
    for i, (kind, amount) in enumerate(records.with_entities(FleetRecord.kind, func.sum(FleetRecord.amount_cents)).group_by(FleetRecord.kind).order_by(FleetRecord.kind).all()):
        costs.append({"kind": kind, "label": COSTS[kind], "cents": amount, "value": money(amount),
                      "percent": round(amount * 100 / total, 2) if total else 0, "color": COLORS[i % len(COLORS)]})
    cursor, slices = 0, []
    for cost in costs:
        stop = cursor + cost["percent"]
        slices.append(f"{cost['color']} {cursor:.2f}% {stop:.2f}%")
        cursor = stop
    donut = "conic-gradient(" + ",".join(slices) + ")" if slices else "var(--border)"
    vehicle_costs = dict(records.with_entities(FleetRecord.vehicle_id, func.sum(FleetRecord.amount_cents)).group_by(FleetRecord.vehicle_id).all())
    vehicle_distances = dict(db.session.query(Trip.vehicle_id, func.sum(Trip.distance_m)).filter(trip_filter).group_by(Trip.vehicle_id).all())
    vehicle_query = Vehicle.query
    if vehicle_id is not None:
        vehicle_query = vehicle_query.filter_by(id=vehicle_id)
    elif driver_id is not None:
        vehicle_query = vehicle_query.filter(Vehicle.id.in_((set(vehicle_costs) | set(vehicle_distances)) - {None}))
    vehicles = [{"vehicle": vehicle, "cents": vehicle_costs.get(vehicle.id, 0), "distance_m": vehicle_distances.get(vehicle.id, 0)} for vehicle in vehicle_query.order_by(Vehicle.nickname).all()]
    grouped_orders = dict(db.session.query(ServiceOrder.driver_id, func.count()).filter(order_filter, ServiceOrder.status == "done").group_by(ServiceOrder.driver_id).all())
    grouped_service = dict(db.session.query(ServiceOrder.driver_id, func.avg(ServiceOrder.service_minutes)).filter(order_filter, ServiceOrder.status == "done").group_by(ServiceOrder.driver_id).all())
    trip_stats = {row[0]: row[1:] for row in db.session.query(Trip.driver_id, func.sum(Trip.distance_m), func.sum(Trip.transit_minutes), func.max(Trip.lunch_minutes), func.sum(Trip.deviations)).filter(trip_filter).group_by(Trip.driver_id).all()}
    driver_ids = {row[0] for row in db.session.query(ServiceOrder.driver_id).filter(order_filter).distinct()} | set(trip_stats)
    drivers = []
    for driver in Driver.query.filter(Driver.id.in_(driver_ids)).order_by(Driver.name).all():
        distance_m, transit, lunch, deviations = trip_stats.get(driver.id, (0, 0, 0, 0))
        drivers.append({"driver": driver, "completed": grouped_orders.get(driver.id, 0), "distance_m": distance_m,
                        "transit": transit, "lunch": lunch, "deviations": deviations,
                        "service": round(grouped_service.get(driver.id, 0) or 0)})
    # SQL aggregation by actual dates; costs and OS use separate unit scales.
    group_format = "%Y-%m" if (end - start).days > 30 else "%Y-%m-%d"
    order_bucket = func.strftime(group_format, ServiceOrder.date)
    expense_bucket = func.strftime(group_format, FleetRecord.date)
    order_points = dict(db.session.query(order_bucket, func.count()).filter(order_filter, ServiceOrder.status == "done").group_by(order_bucket).all())
    cost_points = dict(records.with_entities(expense_bucket, func.sum(FleetRecord.amount_cents)).group_by(expense_bucket).all())
    buckets = []
    cursor_date = start
    while cursor_date <= end:
        key = cursor_date.strftime(group_format)
        if key not in buckets:
            buckets.append(key)
        cursor_date += timedelta(days=1)
    series = [{"label": key[8:] + "/" + key[5:7] if len(key) == 10 else key[5:] + "/" + key[:4],
               "orders": order_points.get(key, 0), "cents": cost_points.get(key, 0)} for key in buckets]
    max_orders = max((x["orders"] for x in series), default=0) or 1
    max_costs = max((x["cents"] for x in series), default=0) or 1
    for item in series:
        item.update(order_height=round(item["orders"] * 100 / max_orders, 2), cost_height=round(item["cents"] * 100 / max_costs, 2))
    max_completed = max((d["completed"] for d in drivers), default=0) or 1
    for driver in drivers:
        driver["bar"] = driver["completed"] * 100 / max_completed
    fuel_points = []
    for date, weighted, volume in records.filter(FleetRecord.kind == "combustivel").with_entities(
        FleetRecord.date, func.sum(FleetRecord.price_cents * FleetRecord.fuel_ml), func.sum(FleetRecord.fuel_ml)
    ).group_by(FleetRecord.date).order_by(FleetRecord.date).all():
        fuel_points.append({"date": date, "cents": int((Decimal(weighted) / volume).quantize(Decimal("1"), rounding=ROUND_HALF_UP))})
    fuel_axis = max(100, ((max((p["cents"] for p in fuel_points), default=0) + 99) // 100) * 100)
    for i, point in enumerate(fuel_points):
        point.update(x=50 + i * 450 / max(len(fuel_points) - 1, 1), y=180 - point["cents"] * 140 / fuel_axis)
    time_rows = {row[0]: {"transit": row[1], "lunch": row[2], "service": 0} for row in db.session.query(
        Trip.driver_id, func.sum(Trip.transit_minutes), func.sum(Trip.lunch_minutes)).filter(trip_filter).group_by(Trip.driver_id).all()}
    for driver_id, minutes in db.session.query(ServiceOrder.driver_id, func.sum(ServiceOrder.service_minutes)).filter(
        order_filter, ServiceOrder.status == "done").group_by(ServiceOrder.driver_id).all():
        time_rows.setdefault(driver_id, {"transit": 0, "lunch": 0, "service": 0})["service"] = minutes
    max_time = max((sum(row.values()) for row in time_rows.values()), default=0) or 1
    for driver in drivers:
        times = time_rows.get(driver["driver"].id, {"transit": 0, "lunch": 0, "service": 0})
        driver["times"] = times
        driver["time_widths"] = {key: value * 100 / max_time for key, value in times.items()}
    for row in vehicles:
        row["cost_per_km"] = int((Decimal(row["cents"]) * 1000 / row["distance_m"]).quantize(Decimal("1"), rounding=ROUND_HALF_UP)) if row["distance_m"] else None
    ranking = sorted((row for row in vehicles if row["cost_per_km"] is not None), key=lambda row: row["cost_per_km"], reverse=True)
    max_ratio = max((row["cost_per_km"] for row in ranking), default=0) or 1
    for row in ranking:
        row["width"] = row["cost_per_km"] * 100 / max_ratio
    trip_count = Trip.query.filter(trip_filter).count()
    lunch_excesses = Trip.query.filter(trip_filter, Trip.lunch_minutes > 120).count()
    deviations = db.session.query(func.coalesce(func.sum(Trip.deviations), 0)).filter(trip_filter).scalar()
    maintenance = FleetRecord.query.filter(record_filter, FleetRecord.kind == "manutencao")
    return dict(total_cents=total, distance_m=distance, fuel_ml=fuel_ml, complete=complete, orders_total=orders_total,
                service_average=round(service_average or 0), completion=round(100 * complete / orders_total) if orders_total else 0,
                cost_per_km=int((Decimal(total) * 1000 / distance).quantize(Decimal("1"), rounding=ROUND_HALF_UP)) if distance else None,
                fuel_points=fuel_points, fuel_axis=fuel_axis, ranking=ranking,
                costs=costs, donut=donut, vehicles=vehicles, drivers=drivers, series=series, statuses=statuses,
                unattributed_cents=vehicle_costs.get(None, 0), start=start, end=end,
                trip_count=trip_count, lunch_excesses=lunch_excesses, deviations=deviations,
                completed_maintenance=maintenance.filter_by(status="posted").count(),
                scheduled_maintenance=maintenance.filter_by(status="scheduled").count(),
                record_count=records.count(),
                scheduled_cents=FleetRecord.query.filter(record_filter, FleetRecord.status == "scheduled").with_entities(func.coalesce(func.sum(FleetRecord.amount_cents), 0)).scalar())


def active_alerts(user_id, day=None):
    day = day or today()
    alerts = []
    for trip in Trip.query.filter_by(date=day).filter(Trip.deviations > 0).all():
        alerts.append(dict(id=f"deviation:{trip.id}", category="routes", title="Desvio registrado", level="medium",
                           description=f"{trip.driver.name}: {trip.deviations} ocorrência(s) para conferir.",
                           url=f"/rotas?data={day.isoformat()}&colaborador={trip.driver_id}"))
    for trip in Trip.query.filter_by(date=day).filter(Trip.lunch_minutes > 120).all():
        alerts.append(dict(id=f"lunch:{trip.id}", category="routes", title="Almoço acima de 2 horas", level="high",
                           description=f"{trip.driver.name}: {trip.lunch_minutes} minutos; {trip.lunch_minutes - 120} minutos acima do limite.",
                           url=f"/rotas?data={day.isoformat()}&colaborador={trip.driver_id}"))
    for order in ServiceOrder.query.filter_by(date=day, status="late").all():
        alerts.append(dict(id=f"order-late:{order.id}", category="routes", title="Ordem atrasada", level="medium",
                           description=f"{order.code} · {order.customer}", url=f"/ordens/{order.id}"))
    latest_oil = db.select(FleetRecord.vehicle_id, func.max(FleetRecord.date).label("last_date")).where(FleetRecord.kind == "oleo").group_by(FleetRecord.vehicle_id).subquery()
    oil_records = FleetRecord.query.join(latest_oil, (FleetRecord.vehicle_id == latest_oil.c.vehicle_id) & (FleetRecord.date == latest_oil.c.last_date)).filter(FleetRecord.kind == "oleo").all()
    # Same-day entries are resolved by ID, avoiding duplicate warnings.
    latest = {}
    for record in oil_records:
        if record.vehicle_id not in latest or latest[record.vehicle_id].id < record.id:
            latest[record.vehicle_id] = record
    for record in latest.values():
        remaining = record.next_odometer - record.vehicle.odometer if record.next_odometer else None
        if (remaining is not None and remaining <= 500) or (record.next_date and record.next_date <= day + timedelta(days=7)):
            alerts.append(dict(id=f"oil:{record.id}", category="fleet", title="Troca de óleo próxima", level="high" if remaining is not None and remaining <= 0 else "medium",
                               description=f"{record.vehicle.nickname} · próxima troca em {record.next_date.strftime('%d/%m/%Y')} ou {record.next_odometer} km.", url="/frota"))
    for record in FleetRecord.query.filter(FleetRecord.status == "scheduled", FleetRecord.date <= day + timedelta(days=7)).all():
        alerts.append(dict(id=f"maintenance:{record.id}", category="fleet", title="Manutenção pendente" if record.date < day else "Manutenção próxima", level="high" if record.date < day else "medium",
                           description=f"{record.vehicle.nickname} · {record.subtype} · {record.date.strftime('%d/%m/%Y')}", url="/frota#maintenance"))
    ids = [item["id"] for item in alerts]
    acknowledged = {row.occurrence_id for row in AlertAcknowledgement.query.filter(AlertAcknowledgement.user_id == user_id, AlertAcknowledgement.occurrence_id.in_(ids)).all()}
    for item in alerts:
        item["acknowledged"] = item["id"] in acknowledged
    return alerts
