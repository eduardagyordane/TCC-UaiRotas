"""Shared server-side validation. Never trust HTML constraints alone."""
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from flask import current_app


def today():
    return datetime.now(ZoneInfo(current_app.config["TIMEZONE"])).date()


def digits(value):
    return re.sub(r"[^0-9]", "", value or "")


def valid_cpf(value):
    value = digits(value)
    if len(value) != 11 or len(set(value)) == 1:
        return False
    for length in (9, 10):
        total = sum(int(n) * (length + 1 - i) for i, n in enumerate(value[:length]))
        check = (total * 10 % 11) % 10
        if check != int(value[length]):
            return False
    return True


def valid_email(value):
    return len(value) <= 255 and re.fullmatch(r"[^\s@]+@[^\s@.]+(?:\.[^\s@.]+)+", value) is not None


def valid_phone(value):
    number = digits(value)
    return len(number) in (10, 11) and number[:2] not in {"00", "01"} and len(set(number)) > 1


class Form:
    def __init__(self, values):
        self.values = values
        self.errors = {}

    def text(self, name, label, max_length=120, required=True):
        value = self.values.get(name, "").strip()
        if required and not value:
            self.errors[name] = f"Preencha {label}."
        elif len(value) > max_length:
            self.errors[name] = f"{label}: utilize no máximo {max_length} caracteres."
        return value

    def number(self, name, label, scale=1, minimum=0, maximum=10_000_000, required=True):
        raw = self.text(name, label, 30, required)
        if not raw and not required:
            return None
        try:
            number = Decimal(raw.replace(",", "."))
            if not number.is_finite() or not Decimal(str(minimum)) <= number <= Decimal(str(maximum)):
                raise ValueError
            scaled = number * scale
            if scaled != scaled.to_integral_value():
                raise ValueError
            return int(scaled)
        except (InvalidOperation, ValueError):
            self.errors[name] = f"{label}: informe um número válido entre {minimum} e {maximum}, com a precisão indicada."
            return None

    def date(self, name, label, required=True, past=False):
        raw = self.text(name, label, 10, required)
        if not raw and not required:
            return None
        try:
            value = date.fromisoformat(raw)
            if value.year < 1900 or (past and value > today()):
                raise ValueError
            return value
        except ValueError:
            self.errors[name] = f"{label}: informe uma data válida" + (", até hoje." if past else ".")
            return None

    def choice(self, name, label, choices, required=True):
        value = self.text(name, label, 80, required)
        if value and value not in choices:
            self.errors[name] = f"{label}: selecione uma opção válida."
        return value

    def relation(self, name, label, model, required=True):
        from .extensions import db
        raw = self.text(name, label, 20, required)
        if not raw and not required:
            return None
        obj = db.session.get(model, int(raw)) if raw.isascii() and raw.isdigit() and len(raw) < 12 else None
        if obj is None:
            self.errors[name] = f"{label}: selecione um cadastro existente."
        return obj


def fuel_total(fuel_ml, price_cents):
    return int((Decimal(fuel_ml) * Decimal(price_cents) / 1000).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def money(cents):
    value = Decimal(cents or 0) / 100
    return "R$ " + f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def decimal_br(value, places=1):
    return f"{value:,.{places}f}".replace(",", "_").replace(".", ",").replace("_", ".")
