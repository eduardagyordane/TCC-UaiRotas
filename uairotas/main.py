from datetime import date

from flask import Blueprint, render_template
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
