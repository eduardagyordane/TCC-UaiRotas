import csv
from datetime import timedelta
from io import StringIO
import uuid

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from .analytics import COSTS, STATUS, active_alerts, period, report_conditions, report_data, report_filters, route_context, selected_date, source_info
from .extensions import db
from .fleet_service import KINDS, SUCCESS, build_record
from .models import AlertAcknowledgement, AuditLog, Driver, FleetRecord, Place, ServiceOrder, Trip, User, Vehicle
from .users import page_number, require_admin
from .validation import Form, today

main_bp = Blueprint("main", __name__)


@main_bp.app_context_processor
def common_context():
    return {"status_labels": STATUS, "cost_labels": COSTS, "uuid": lambda: str(uuid.uuid4())}


@main_bp.get("/")
@login_required
def home():
    day = today()
    data = route_context(day)
    overview = report_data(day, day)
    alerts = active_alerts(current_user.id)
    return render_template("home.html", **data, overview=overview, alerts=alerts,
                           vehicle_count=Vehicle.query.count(), driver_count=Driver.query.count(),
                           source=source_info(), today=day)


@main_bp.get("/rotas")
@login_required
def routes():
    day = selected_date()
    driver_raw = request.args.get("colaborador", "todos")
    status = request.args.get("status", "todos")
    if status != "todos" and status not in STATUS:
        abort(400)
    driver = None
    if driver_raw != "todos":
        form = Form({"driver": driver_raw})
        driver = form.relation("driver", "Colaborador", Driver)
        if form.errors:
            abort(400)
    data = route_context(day, driver.id if driver else None, status if status != "todos" else None)
    alerts = [alert for alert in active_alerts(current_user.id, day) if alert["category"] == "routes"]
    if driver or status != "todos":
        allowed = {f"{kind}:{t.id}" for t in data["trips"] for kind in ("lunch", "deviation")} | {f"order-late:{o.id}" for o in data["orders"]}
        alerts = [alert for alert in alerts if alert["id"] in allowed]
    return render_template("routes.html", **data, drivers=Driver.query.order_by(Driver.name).all(),
                           selected_collaborator=driver_raw, selected_status=status, selected_date=day,
                           source=source_info(), alerts=alerts)


@main_bp.get("/ordens/<int:order_id>")
@login_required
def order_detail(order_id):
    order = db.get_or_404(ServiceOrder, order_id)
    return render_template("order.html", order=order)


def render_fleet(values=None, errors=None, kind=None, status=200):
    day = today()
    overview = report_data(day.replace(day=1), day)
    vehicle_query = Vehicle.query.order_by(Vehicle.nickname)
    vehicle_page = vehicle_query.paginate(page=page_number(), per_page=25, error_out=False)
    all_vehicles = vehicle_query.all()
    last_oil = {}
    for record in FleetRecord.query.filter_by(kind="oleo").order_by(FleetRecord.date, FleetRecord.id).all():
        last_oil[record.vehicle_id] = record
    history_query = FleetRecord.query.order_by(FleetRecord.date.desc(), FleetRecord.id.desc())
    filter_kind = request.args.get("tipo", "todos")
    if filter_kind != "todos":
        if filter_kind not in COSTS:
            abort(400)
        history_query = history_query.filter_by(kind=filter_kind)
    history_page = request.args.get("historico", "1")
    if not history_page.isascii() or not history_page.isdigit() or len(history_page) > 6 or int(history_page) < 1:
        abort(400)
    history = history_query.paginate(page=int(history_page), per_page=25, error_out=False)
    return render_template("fleet.html", vehicles=vehicle_page.items, pagination=vehicle_page,
                           vehicle_options=all_vehicles, drivers=Driver.query.order_by(Driver.name).all(),
                           last_oil=last_oil, overview=overview, history=history, filter_kind=filter_kind,
                           maintenance=FleetRecord.query.filter_by(status="scheduled").order_by(FleetRecord.date).all(),
                           last_fuel=FleetRecord.query.filter_by(kind="combustivel").order_by(FleetRecord.date.desc(), FleetRecord.id.desc()).first(),
                           places=Place.query.order_by(Place.name).all(), source=source_info(),
                           form_values=values or {}, errors=errors or {}, active_kind=kind, kinds=KINDS,
                           alerts=[a for a in active_alerts(current_user.id) if a["category"] == "fleet"], today=day), status


@main_bp.get("/frota")
@login_required
def fleet():
    return render_fleet()


@main_bp.post("/frota/registros/<record_type>")
@login_required
def create_fleet_record(record_type):
    require_admin()
    if record_type not in KINDS:
        abort(404)
    record, errors = build_record(record_type, request.form, request.files, current_user)
    values = {key: value for key, value in request.form.items() if key != "csrf_token"}
    if errors:
        return render_fleet(values, errors, record_type, 422)
    if isinstance(record, FleetRecord) and FleetRecord.query.filter_by(submission_key=record.submission_key).first():
        flash("Este registro já foi salvo.", "info")
        return redirect(url_for("main.fleet"))
    try:
        db.session.add(record)
        if isinstance(record, FleetRecord) and record.vehicle_id and record.odometer is not None:
            vehicle = db.session.get(Vehicle, record.vehicle_id)
            if record.date >= vehicle.reading_date:
                vehicle.odometer = record.odometer
                vehicle.reading_date = record.date
        db.session.flush()
        db.session.add(AuditLog(actor_id=current_user.id, action="create", entity=record_type, entity_id=record.id))
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return render_fleet(values, {"_form": "Este cadastro já existe ou foi salvo em outra solicitação. Confira a listagem."}, record_type, 409)
    flash(SUCCESS[record_type], "success")
    return redirect(url_for("main.fleet"))


@main_bp.post("/frota/manutencoes/<int:record_id>/concluir")
@login_required
def complete_maintenance(record_id):
    require_admin()
    record = db.get_or_404(FleetRecord, record_id)
    if record.kind != "manutencao" or record.status != "scheduled":
        abort(400)
    form = Form(request.form)
    completed_date = form.date("data", "Data da realização", past=True)
    actual_cost = form.number("valor", "Valor pago", scale=100, minimum=0.01, maximum=1_000_000)
    if form.errors:
        return render_template("maintenance.html", record=record, errors=form.errors, form_values=request.form, today=today()), 422
    record.date, record.amount_cents, record.status = completed_date, actual_cost, "posted"
    db.session.add(AuditLog(actor_id=current_user.id, action="complete", entity="manutencao", entity_id=record.id))
    db.session.commit()
    flash("Manutenção concluída e incluída nos custos pela data de realização.", "success")
    return redirect(url_for("main.fleet"))


@main_bp.get("/frota/manutencoes/<int:record_id>")
@login_required
def maintenance_detail(record_id):
    require_admin()
    record = db.get_or_404(FleetRecord, record_id)
    if record.kind != "manutencao" or record.status != "scheduled":
        abort(404)
    return render_template("maintenance.html", record=record, errors={}, form_values={}, today=today())


@main_bp.get("/motoristas/<int:driver_id>/foto")
@login_required
def driver_photo(driver_id):
    require_admin()
    driver = db.get_or_404(Driver, driver_id)
    if not driver.photo:
        abort(404)
    return Response(driver.photo, mimetype=driver.photo_mime)


def fleet_values(kind, record):
    if kind == "veiculo":
        fields = {"placa_chassi": "plate", "apelido": "nickname", "marca": "brand", "modelo": "model", "ano": "year",
                  "grupo": "group", "porte": "size", "tipo_mapa": "map_type", "tag": "tag", "odometro": "odometer",
                  "data_cadastro": "reading_date", "hora_leitura": "reading_time", "motorista": "driver_id"}
    elif kind == "motorista":
        fields = {"nome": "name", "contato": "phone", "cpf": "cpf", "cnh": "license_number", "categoria": "category",
                  "primeira_habilitacao": "first_license", "validade": "license_expiry", "matricula": "registration", "identificador": "identifier"}
    else:
        fields = {"veiculo": "vehicle_id", "motorista": "driver_id", "data": "date", "ultima_troca": "date",
                  "quilometragem": "odometer", "proxima_troca": "next_date", "proxima_quilometragem": "next_odometer",
                  "descricao": "description", "observacoes": "description", "posto": "description", "tipo": "subtype"}
    values = {key: getattr(record, attribute) if getattr(record, attribute) is not None else "" for key, attribute in fields.items()}
    if isinstance(record, FleetRecord):
        values.update(valor=f"{record.amount_cents / 100:.2f}", valor_litro=f"{(record.price_cents or 0) / 100:.2f}",
                      litros=f"{(record.fuel_ml or 0) / 1000:.3f}")
    return values


@main_bp.route("/frota/cadastros/<kind>/<int:record_id>/editar", methods=["GET", "POST"])
@login_required
def edit_fleet_record(kind, record_id):
    require_admin()
    if kind not in KINDS:
        abort(404)
    model = Vehicle if kind == "veiculo" else Driver if kind == "motorista" else FleetRecord
    record = db.get_or_404(model, record_id)
    if model is FleetRecord and record.kind != kind:
        abort(404)
    errors = {}
    values = fleet_values(kind, record)
    if request.method == "POST":
        values = {key: value for key, value in request.form.items() if key != "csrf_token"}
        candidate, errors = build_record(kind, values, request.files, current_user, existing=record)
        if isinstance(record, FleetRecord) and record.odometer is not None:
            if any(getattr(candidate, key) != getattr(record, key) for key in ("odometer", "date", "vehicle_id")):
                errors["_form"] = "Preserve veículo, data e quilometragem desta leitura histórica. Registre uma nova leitura para atualizar o odômetro."
        if not errors:
            for column in model.__table__.columns:
                if column.name not in ("id", "source", "created_by", "submission_key"):
                    value = getattr(candidate, column.name)
                    if column.name in ("photo", "photo_mime") and value is None:
                        continue
                    setattr(record, column.name, value)
            db.session.add(AuditLog(actor_id=current_user.id, action="update", entity=kind, entity_id=record.id))
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                errors["_form"] = "Este cadastro conflita com um registro existente. Confira os dados."
            else:
                flash("Cadastro atualizado com sucesso.", "success")
                return redirect(url_for("main.fleet"))
    history = db.session.query(AuditLog, User.name).outerjoin(User, User.id == AuditLog.actor_id).filter(
        AuditLog.entity == kind, AuditLog.entity_id == record_id).order_by(AuditLog.created_at.desc()).limit(20).all()
    return render_template("fleet_edit.html", kind=kind, record=record, v=values, e=errors, prefix="edit-", today=today(),
                           kinds=KINDS, vehicle_options=Vehicle.query.order_by(Vehicle.nickname).all(),
                           drivers=Driver.query.order_by(Driver.name).all(), history=history), 422 if errors else 200


@main_bp.get("/alertas")
@login_required
def alerts():
    return render_template("alerts.html", alerts=active_alerts(current_user.id), source=source_info())


@main_bp.post("/alertas/reconhecer")
@login_required
def acknowledge_alert():
    occurrence_id = request.form.get("occurrence_id", "")
    if occurrence_id not in {item["id"] for item in active_alerts(current_user.id)}:
        abort(400)
    key = (current_user.id, occurrence_id)
    if db.session.get(AlertAcknowledgement, key) is None:
        db.session.add(AlertAcknowledgement(user_id=current_user.id, occurrence_id=occurrence_id))
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
    flash("Alerta marcado como visto. A ocorrência continuará visível enquanto estiver pendente.", "success")
    return redirect(url_for("main.alerts"))


def render_report(module):
    selected, periods, start, end = period()
    vehicle, driver = report_filters()
    vehicle_id, driver_id = vehicle.id if vehicle else None, driver.id if driver else None
    params = {"periodo": selected}
    if vehicle:
        params["veiculo"] = vehicle.id
    if driver:
        params["motorista"] = driver.id
    records = None
    if module == "fleet":
        condition, _, _ = report_conditions(start, end, vehicle_id, driver_id)
        records = FleetRecord.query.filter(condition).order_by(FleetRecord.date.desc(), FleetRecord.id.desc()).paginate(
            page=page_number(), per_page=25, error_out=False)
    return render_template("reports.html", module=module,
                           overview=report_data(start, end, vehicle_id, driver_id), selected_period=selected, periods=periods,
                           vehicle_options=Vehicle.query.order_by(Vehicle.nickname).all(),
                           driver_options=Driver.query.order_by(Driver.name).all(), selected_vehicle=vehicle, selected_driver=driver,
                           filter_params=params, source=source_info(), records=records)


@main_bp.get("/relatorios")
@login_required
def reports():
    return render_report("overview")


@main_bp.get("/relatorios/frota")
@login_required
def fleet_reports():
    return render_report("fleet")


@main_bp.get("/relatorios/rotas")
@login_required
def route_reports():
    return render_report("routes")


def csv_safe(value):
    text = str(value)
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else text


@main_bp.get("/relatorios/<module>/exportar.csv")
@login_required
def export_report(module):
    if module not in ("overview", "fleet", "routes"):
        abort(404)
    _, _, start, end = period()
    vehicle, driver = report_filters()
    data = report_data(start, end, vehicle.id if vehicle else None, driver.id if driver else None)
    output = StringIO(newline="")
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["UaiRotas", source_info()["label"], start.isoformat(), end.isoformat(),
                     "Veículo", csv_safe(vehicle.nickname + " · " + vehicle.plate) if vehicle else "Todos",
                     "Motorista", csv_safe(driver.name) if driver else "Todos"])
    if module == "fleet":
        writer.writerow(["Veículo", "Placa/chassi", "Distância (m)", "Custo (centavos)"])
        for row in data["vehicles"]:
            writer.writerow([csv_safe(row["vehicle"].nickname), csv_safe(row["vehicle"].plate), row["distance_m"], row["cents"]])
        writer.writerow(["Sem veículo vinculado", "", 0, data["unattributed_cents"]])
    elif module == "routes":
        writer.writerow(["Colaborador", "OS concluídas", "Distância (m)", "Trânsito (min)", "Maior almoço (min)", "Desvios"])
        for row in data["drivers"]:
            writer.writerow([csv_safe(row["driver"].name), row["completed"], row["distance_m"], row["transit"], row["lunch"], row["deviations"]])
    else:
        writer.writerow(["Período", "OS concluídas", "Custos (centavos)"])
        writer.writerows((row["label"], row["orders"], row["cents"]) for row in data["series"])
    return Response("\ufeff" + output.getvalue(), mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="uairotas-{module}-{start}-{end}.csv"'})
