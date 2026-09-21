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


def _selected_report_period():
    periods = {
        "7dias": "Últimos 7 dias",
        "30dias": "Últimos 30 dias",
        "90dias": "Últimos 90 dias",
        "ano": "Ano de 2026",
    }
    selected = request.args.get("periodo", "30dias")
    if selected not in periods:
        selected = "30dias"
    return selected, periods


@main_bp.get("/relatorios")
@login_required
def reports():
    selected_period, periods = _selected_report_period()
    metrics = [
        {"label": "Ordens concluídas", "value": "486", "detail": "+11,8%", "trend": "up", "tone": "red"},
        {"label": "Quilometragem rodada", "value": "4.826 km", "detail": "+8,4%", "trend": "up", "tone": "blue"},
        {"label": "Custo operacional", "value": "R$ 12.116,70", "detail": "−3,2%", "trend": "down", "tone": "yellow"},
        {"label": "Tempo médio por OS", "value": "1h24", "detail": "−9 min", "trend": "down", "tone": "green"},
    ]
    monthly = [
        {"month": "Abr", "orders": 328, "distance": 3220},
        {"month": "Mai", "orders": 351, "distance": 3540},
        {"month": "Jun", "orders": 389, "distance": 3870},
        {"month": "Jul", "orders": 412, "distance": 4210},
        {"month": "Ago", "orders": 448, "distance": 4550},
        {"month": "Set", "orders": 486, "distance": 4826},
    ]
    report_cards = [
        {
            "title": "Relatório de rotas",
            "description": "Produtividade, deslocamentos, ordens, tempos e desvios por colaborador.",
            "value": "91%",
            "label": "aderência às rotas",
            "endpoint": "main.route_reports",
            "tone": "red",
        },
        {
            "title": "Relatório de frota",
            "description": "Custos, combustível, quilometragem, multas e manutenções dos veículos.",
            "value": "R$ 2,51",
            "label": "custo médio por km",
            "endpoint": "main.fleet_reports",
            "tone": "blue",
        },
    ]
    alerts = [
        {"label": "Almoços acima de 2 horas", "value": "5", "detail": "2 a menos que no período anterior", "tone": "warning"},
        {"label": "Manutenções vencendo", "value": "3", "detail": "1 veículo com prioridade alta", "tone": "danger"},
        {"label": "Desvios de rota", "value": "9", "detail": "−18% no período", "tone": "info"},
    ]
    return render_template(
        "reports_overview.html",
        metrics=metrics,
        monthly=monthly,
        report_cards=report_cards,
        alerts=alerts,
        periods=periods,
        selected_period=selected_period,
    )


@main_bp.get("/relatorios/frota")
@login_required
def fleet_reports():
    selected_period, periods = _selected_report_period()
    metrics = [
        {"label": "Custo total", "value": "R$ 12.116,70", "detail": "−3,2%", "trend": "down", "tone": "red"},
        {"label": "Custo por km", "value": "R$ 2,51", "detail": "−R$ 0,18", "trend": "down", "tone": "blue"},
        {"label": "Consumo médio", "value": "10,8 km/L", "detail": "+0,6 km/L", "trend": "up", "tone": "green"},
        {"label": "Manutenções", "value": "7", "detail": "3 programadas", "trend": "neutral", "tone": "yellow"},
    ]
    costs = [
        {"label": "Combustível", "value": "R$ 8.420,30", "percent": 69, "tone": "red"},
        {"label": "Manutenções", "value": "R$ 2.180,00", "percent": 18, "tone": "yellow"},
        {"label": "Outros gastos", "value": "R$ 930,00", "percent": 8, "tone": "purple"},
        {"label": "Multas", "value": "R$ 586,40", "percent": 5, "tone": "blue"},
    ]
    fuel_history = [
        {"month": "Abr", "price": "5,72", "height": 42},
        {"month": "Mai", "price": "5,84", "height": 49},
        {"month": "Jun", "price": "5,91", "height": 55},
        {"month": "Jul", "price": "6,03", "height": 64},
        {"month": "Ago", "price": "6,11", "height": 72},
        {"month": "Set", "price": "6,19", "height": 80},
    ]
    vehicles = [
        {"vehicle": "Strada 01", "plate": "QWE-4J21", "driver": "Carlos Mendes", "distance": "1.486 km", "fuel": "11,6 km/L", "cost": "R$ 3.248,20", "maintenance": "Em dia", "status": "good"},
        {"vehicle": "Saveiro 02", "plate": "RTY-8A13", "driver": "Ana Paula", "distance": "1.279 km", "fuel": "10,9 km/L", "cost": "R$ 3.510,40", "maintenance": "Vence em 220 km", "status": "warning"},
        {"vehicle": "Oroch 03", "plate": "GHT-2D09", "driver": "Marcos Silva", "distance": "1.164 km", "fuel": "9,8 km/L", "cost": "R$ 3.126,80", "maintenance": "Agendada", "status": "scheduled"},
        {"vehicle": "Fiorino 04", "plate": "HJK-7F42", "driver": "Sem motorista", "distance": "897 km", "fuel": "10,5 km/L", "cost": "R$ 2.231,30", "maintenance": "Em dia", "status": "good"},
    ]
    return render_template(
        "reports_fleet.html",
        metrics=metrics,
        costs=costs,
        fuel_history=fuel_history,
        vehicles=vehicles,
        periods=periods,
        selected_period=selected_period,
    )


@main_bp.get("/relatorios/rotas")
@login_required
def route_reports():
    selected_period, periods = _selected_report_period()
    metrics = [
        {"label": "Distância percorrida", "value": "4.826 km", "detail": "+8,4%", "trend": "up", "tone": "red"},
        {"label": "Ordens concluídas", "value": "486", "detail": "92% do total", "trend": "up", "tone": "blue"},
        {"label": "Aderência às rotas", "value": "91%", "detail": "+4 pontos", "trend": "up", "tone": "green"},
        {"label": "Tempo médio em trânsito", "value": "2h17", "detail": "−12 min", "trend": "down", "tone": "yellow"},
    ]
    collaborators = [
        {"name": "Carlos Mendes", "initials": "CM", "vehicle": "QWE-4J21", "distance": "1.486 km", "completed": 168, "completion": 96, "transit": "2h04", "service": "1h18", "lunch": "1h08", "deviations": 1, "tone": "red"},
        {"name": "Ana Paula", "initials": "AP", "vehicle": "RTY-8A13", "distance": "1.279 km", "completed": 154, "completion": 92, "transit": "2h12", "service": "1h26", "lunch": "1h17", "deviations": 3, "tone": "blue"},
        {"name": "Marcos Silva", "initials": "MS", "vehicle": "GHT-2D09", "distance": "1.164 km", "completed": 139, "completion": 86, "transit": "2h35", "service": "1h31", "lunch": "2h18", "deviations": 5, "tone": "yellow"},
        {"name": "Rafael Lima", "initials": "RL", "vehicle": "HJK-7F42", "distance": "897 km", "completed": 125, "completion": 89, "transit": "2h21", "service": "1h22", "lunch": "1h12", "deviations": 0, "tone": "purple"},
    ]
    daily_times = [
        {"day": "Seg", "minutes": 151, "height": 74},
        {"day": "Ter", "minutes": 143, "height": 65},
        {"day": "Qua", "minutes": 132, "height": 54},
        {"day": "Qui", "minutes": 139, "height": 61},
        {"day": "Sex", "minutes": 128, "height": 49},
        {"day": "Sáb", "minutes": 112, "height": 35},
    ]
    return render_template(
        "reports_routes.html",
        metrics=metrics,
        collaborators=collaborators,
        daily_times=daily_times,
        periods=periods,
        selected_period=selected_period,
    )
