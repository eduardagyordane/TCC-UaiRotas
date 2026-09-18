from datetime import date

from flask import Blueprint, render_template, request
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
