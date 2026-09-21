from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
@login_required
def home():
    metrics = [
        {"label": "Veículos ativos", "value": "18", "detail": "16 em rota", "icon": "car", "tone": "wine"},
        {"label": "Técnicos em campo", "value": "12", "detail": "3 equipes", "icon": "users", "tone": "yellow"},
        {"label": "Ordens de serviço", "value": "27", "detail": "19 concluídas", "icon": "clipboard", "tone": "blue"},
        {"label": "Alertas ativos", "value": "3", "detail": "1 prioritário", "icon": "alert", "tone": "red"},
    ]

    service_orders = [
        {
            "code": "OS 10482",
            "customer": "Marina Oliveira",
            "service": "Instalação de fibra",
            "technician": "Carlos Mendes",
            "time": "08:30",
            "status": "Em atendimento",
            "status_key": "progress",
        },
        {
            "code": "OS 10496",
            "customer": "Mercado São Lucas",
            "service": "Manutenção de enlace",
            "technician": "Ana Paula",
            "time": "10:00",
            "status": "A caminho",
            "status_key": "route",
        },
        {
            "code": "OS 10503",
            "customer": "João Batista",
            "service": "Suporte técnico",
            "technician": "Rafael Lima",
            "time": "11:30",
            "status": "Agendada",
            "status_key": "scheduled",
        },
    ]

    alerts = [
        {
            "title": "Almoço acima de 2 horas",
            "description": "Marcos Silva está parado há 2h18.",
            "time": "Agora",
            "level": "high",
        },
        {
            "title": "Manutenção próxima",
            "description": "Veículo QWE-4J21 vence em 450 km.",
            "time": "Há 18 min",
            "level": "medium",
        },
        {
            "title": "Rota com atraso",
            "description": "Equipe Norte está 24 min atrasada.",
            "time": "Há 32 min",
            "level": "low",
        },
    ]

    today = date.today().strftime("%d/%m/%Y")
    return render_template(
        "home.html",
        metrics=metrics,
        service_orders=service_orders,
        alerts=alerts,
        today=today,
    )


@main_bp.get("/rotas")
@login_required
def routes():
    collaborators = [
        {
            "id": "carlos",
            "name": "Carlos Mendes",
            "vehicle": "Fiat Strada · QWE-4J21",
            "color": "#d9233f",
            "status": "Em atendimento",
            "status_key": "progress",
            "distance": "38,4 km",
            "orders": 4,
            "completed": 3,
        },
        {
            "id": "ana",
            "name": "Ana Paula",
            "vehicle": "VW Saveiro · RTY-8A13",
            "color": "#2d78b7",
            "status": "A caminho",
            "status_key": "route",
            "distance": "27,8 km",
            "orders": 3,
            "completed": 1,
        },
        {
            "id": "marcos",
            "name": "Marcos Silva",
            "vehicle": "Renault Oroch · GHT-2D09",
            "color": "#d18d14",
            "status": "Parado há 2h18",
            "status_key": "alert",
            "distance": "19,2 km",
            "orders": 3,
            "completed": 2,
        },
    ]

    orders = [
        {
            "code": "OS 10482",
            "customer": "Marina Oliveira",
            "address": "Rua Major Gote, 945 — Centro",
            "service": "Instalação de fibra",
            "collaborator": "carlos",
            "technician": "Carlos Mendes",
            "time": "08:30",
            "status": "Em atendimento",
            "status_key": "progress",
            "sequence": 1,
        },
        {
            "code": "OS 10491",
            "customer": "Clínica Vida",
            "address": "Av. Getúlio Vargas, 622 — Centro",
            "service": "Reparo de conexão",
            "collaborator": "carlos",
            "technician": "Carlos Mendes",
            "time": "10:20",
            "status": "Agendada",
            "status_key": "scheduled",
            "sequence": 2,
        },
        {
            "code": "OS 10496",
            "customer": "Mercado São Lucas",
            "address": "Rua dos Guaranis, 130 — Caramuru",
            "service": "Manutenção de enlace",
            "collaborator": "ana",
            "technician": "Ana Paula",
            "time": "10:00",
            "status": "A caminho",
            "status_key": "route",
            "sequence": 1,
        },
        {
            "code": "OS 10503",
            "customer": "João Batista",
            "address": "Rua Formiga, 418 — Lagoa Grande",
            "service": "Suporte técnico",
            "collaborator": "ana",
            "technician": "Ana Paula",
            "time": "11:30",
            "status": "Agendada",
            "status_key": "scheduled",
            "sequence": 2,
        },
        {
            "code": "OS 10511",
            "customer": "Padaria Tradição",
            "address": "Av. Brasil, 1510 — Caiçaras",
            "service": "Troca de equipamento",
            "collaborator": "marcos",
            "technician": "Marcos Silva",
            "time": "13:30",
            "status": "Atrasada",
            "status_key": "late",
            "sequence": 3,
        },
    ]

    selected_collaborator = request.args.get("colaborador", "todos")
    selected_status = request.args.get("status", "todos")
    selected_date = request.args.get("data", date.today().isoformat())

    filtered_orders = orders
    if selected_collaborator != "todos":
        filtered_orders = [
            order for order in filtered_orders if order["collaborator"] == selected_collaborator
        ]
    if selected_status != "todos":
        filtered_orders = [order for order in filtered_orders if order["status_key"] == selected_status]

    return render_template(
        "routes.html",
        collaborators=collaborators,
        orders=filtered_orders,
        selected_collaborator=selected_collaborator,
        selected_status=selected_status,
        selected_date=selected_date,
    )


@main_bp.get("/frota")
@login_required
def fleet():
    summary = [
        {"label": "Veículos cadastrados", "value": "18", "detail": "16 ativos", "tone": "wine"},
        {"label": "Técnicos vinculados", "value": "12", "detail": "3 equipes", "tone": "blue"},
        {"label": "Quilometragem no mês", "value": "4.826 km", "detail": "+8,4%", "tone": "yellow"},
        {"label": "Valor da gasolina", "value": "R$ 6,19", "detail": "último registro", "tone": "green"},
        {"label": "Locais de interesse", "value": "12", "detail": "4 categorias", "tone": "purple"},
    ]

    vehicles = [
        {
            "plate": "QWE-4J21",
            "nickname": "Strada 01",
            "model": "Fiat Strada Freedom 2023",
            "driver": "Carlos Mendes",
            "technician": "Carlos Mendes",
            "odometer": "48.320 km",
            "last_oil": "12/06/2026",
            "next_oil": "50.000 km",
            "status": "Em rota",
            "status_key": "route",
        },
        {
            "plate": "RTY-8A13",
            "nickname": "Saveiro 02",
            "model": "VW Saveiro Robust 2022",
            "driver": "Ana Paula",
            "technician": "Ana Paula",
            "odometer": "61.780 km",
            "last_oil": "03/05/2026",
            "next_oil": "Vence em 220 km",
            "status": "Atenção",
            "status_key": "warning",
        },
        {
            "plate": "GHT-2D09",
            "nickname": "Oroch 03",
            "model": "Renault Oroch Pro 2021",
            "driver": "Marcos Silva",
            "technician": "Marcos Silva",
            "odometer": "72.405 km",
            "last_oil": "22/07/2026",
            "next_oil": "75.000 km",
            "status": "Parado",
            "status_key": "stopped",
        },
        {
            "plate": "HJK-7F42",
            "nickname": "Fiorino 04",
            "model": "Fiat Fiorino Endurance 2022",
            "driver": "Sem motorista",
            "technician": "Sem vínculo",
            "odometer": "39.110 km",
            "last_oil": "18/08/2026",
            "next_oil": "42.000 km",
            "status": "Disponível",
            "status_key": "available",
        },
    ]

    costs = [
        {"label": "Combustível", "value": "R$ 8.420,30", "percent": 72, "tone": "red"},
        {"label": "Manutenções", "value": "R$ 2.180,00", "percent": 39, "tone": "yellow"},
        {"label": "Multas", "value": "R$ 586,40", "percent": 16, "tone": "blue"},
        {"label": "Outros gastos", "value": "R$ 930,00", "percent": 24, "tone": "purple"},
    ]

    maintenance = [
        {"vehicle": "RTY-8A13", "type": "Troca de óleo", "date": "20/09/2026", "value": "R$ 349,90", "urgency": "Alta"},
        {"vehicle": "GHT-2D09", "type": "Revisão preventiva", "date": "26/09/2026", "value": "R$ 680,00", "urgency": "Média"},
        {"vehicle": "HJK-7F42", "type": "Alinhamento", "date": "02/10/2026", "value": "R$ 180,00", "urgency": "Normal"},
    ]

    return render_template(
        "fleet.html",
        summary=summary,
        vehicles=vehicles,
        costs=costs,
        maintenance=maintenance,
        today=date.today().isoformat(),
    )


@main_bp.post("/frota/registros/<record_type>")
@login_required
def create_fleet_record(record_type):
    required_fields = {
        "veiculo": ("placa_chassi", "apelido", "marca", "modelo", "odometro"),
        "motorista": ("nome", "contato", "cpf", "cnh"),
        "oleo": ("veiculo", "ultima_troca", "proxima_troca", "quilometragem", "valor"),
        "combustivel": ("data", "veiculo", "litros", "valor_litro"),
        "multa": ("data", "veiculo", "motorista", "tipo", "descricao", "valor"),
        "gasto": ("data", "tipo", "descricao", "valor"),
        "manutencao": ("data", "veiculo", "tipo", "valor"),
    }
    success_messages = {
        "veiculo": "Veículo registrado com sucesso.",
        "motorista": "Motorista registrado com sucesso.",
        "oleo": "Troca de óleo registrada com sucesso.",
        "combustivel": "Abastecimento registrado com sucesso.",
        "multa": "Multa registrada com sucesso.",
        "gasto": "Gasto registrado com sucesso.",
        "manutencao": "Manutenção agendada com sucesso.",
    }

    if record_type not in required_fields:
        abort(404)

    missing = [field for field in required_fields[record_type] if not request.form.get(field, "").strip()]
    if missing:
        flash("Preencha todos os campos obrigatórios antes de salvar.", "error")
        return redirect(url_for("main.fleet"))

    flash(success_messages[record_type], "success")
    return redirect(url_for("main.fleet"))
