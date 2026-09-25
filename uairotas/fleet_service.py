import re
import uuid
from datetime import time
from io import BytesIO

from .extensions import db
from .models import Driver, FleetRecord, Vehicle
from .validation import Form, digits, fuel_total, today, valid_cpf, valid_phone

KINDS = {"veiculo": ("Novo veículo", "vehicle-dialog"), "motorista": ("Novo motorista", "driver-dialog"),
         "oleo": ("Troca de óleo", "oil-dialog"), "combustivel": ("Abastecimento", "fuel-dialog"),
         "multa": ("Multa", "fine-dialog"), "gasto": ("Outro gasto", "expense-dialog"),
         "manutencao": ("Agendar manutenção", "maintenance-dialog")}
SUCCESS = {"veiculo": "Veículo registrado com sucesso.", "motorista": "Motorista registrado com sucesso.",
           "oleo": "Troca de óleo registrada com sucesso.", "combustivel": "Abastecimento registrado com sucesso.",
           "multa": "Multa registrada com sucesso.", "gasto": "Gasto registrado com sucesso.",
           "manutencao": "Manutenção agendada com sucesso."}


def build_record(kind, values, files, actor, existing=None):
    form = Form(values)
    if kind == "veiculo":
        plate = re.sub(r"[ -]", "", form.text("placa_chassi", "placa ou chassi", 20)).upper()
        if not re.fullmatch(r"(?:[A-Z]{3}[0-9][A-Z0-9][0-9]{2}|[A-HJ-NPR-Z0-9]{17})", plate):
            form.errors["placa_chassi"] = "Informe uma placa brasileira ou chassi com 17 caracteres."
        if Vehicle.query.filter(Vehicle.plate == plate, Vehicle.id != (existing.id if existing else None)).first():
            form.errors["placa_chassi"] = "Este veículo já está cadastrado."
        driver = form.relation("motorista", "Motorista", Driver, False)
        reading_date = form.date("data_cadastro", "Data da leitura", False, past=True) or today()
        reading_time = None
        if values.get("hora_leitura"):
            try:
                reading_time = time.fromisoformat(values["hora_leitura"])
            except ValueError:
                form.errors["hora_leitura"] = "Informe uma hora válida."
        record = Vehicle(plate=plate, nickname=form.text("apelido", "apelido", 80),
                         brand=form.text("marca", "marca", 60), model=form.text("modelo", "modelo", 80),
                         odometer=form.number("odometro", "Odômetro", maximum=9_999_999),
                         year=form.number("ano", "Ano", minimum=1900, maximum=today().year + 1, required=False),
                         group=form.text("grupo", "grupo", 80, False), size=form.choice("porte", "Porte", ("Leve", "Médio", "Pesado"), False),
                         map_type=form.choice("tipo_mapa", "Tipo", ("Carro", "Utilitário", "Moto"), False),
                         tag=form.text("tag", "tag", 80, False), reading_date=reading_date, reading_time=reading_time,
                         driver_id=driver.id if driver else None)
        if existing and record.odometer is not None and record.odometer < existing.odometer:
            form.errors["odometro"] = "O odômetro não pode diminuir."
        if existing and reading_date < existing.reading_date:
            form.errors["data_cadastro"] = "A nova leitura não pode anteceder a atual."
    elif kind == "motorista":
        cpf = digits(form.text("cpf", "CPF", 14))
        phone = digits(form.text("contato", "contato", 20))
        license_number = digits(form.text("cnh", "CNH", 14))
        if not valid_cpf(cpf):
            form.errors["cpf"] = "Informe um CPF válido, com dígitos verificadores corretos."
        if not valid_phone(phone):
            form.errors["contato"] = "Informe um telefone com DDD e 10 ou 11 dígitos."
        if len(license_number) != 11 or len(set(license_number)) == 1:
            form.errors["cnh"] = "Informe os 11 dígitos da CNH."
        if Driver.query.filter(Driver.cpf == cpf, Driver.id != (existing.id if existing else None)).first():
            form.errors["cpf"] = "Já existe um motorista com este CPF."
        if Driver.query.filter(Driver.license_number == license_number, Driver.id != (existing.id if existing else None)).first():
            form.errors["cnh"] = "Já existe um motorista com esta CNH."
        first = form.date("primeira_habilitacao", "1ª habilitação", False, past=True)
        expiry = form.date("validade", "Validade", False)
        if first and expiry and expiry <= first:
            form.errors["validade"] = "A validade deve ser posterior à primeira habilitação."
        record = Driver(name=form.text("nome", "nome", 120), phone=phone, cpf=cpf, license_number=license_number,
                        category=form.choice("categoria", "Categoria", ("A", "B", "AB", "C", "D", "E", "AC", "AD", "AE"), False),
                        first_license=first, license_expiry=expiry, registration=form.text("matricula", "matrícula", 60, False),
                        identifier=form.choice("identificador", "Identificador", ("Nenhum", "Tag NFC", "iButton", "Cartão RFID"), False))
        photo = files.get("foto")
        if photo and photo.filename:
            try:
                from PIL import Image, ImageOps
                raw = photo.read(512 * 1024 + 1)
                if len(raw) > 512 * 1024:
                    raise ValueError
                with Image.open(BytesIO(raw)) as picture:
                    if picture.format not in ("JPEG", "PNG") or picture.width * picture.height > 16_000_000:
                        raise ValueError
                    picture = ImageOps.exif_transpose(picture).convert("RGB")
                    picture.thumbnail((256, 256))
                    result = BytesIO()
                    picture.save(result, format="JPEG", quality=85)
                record.photo = result.getvalue()
                record.photo_mime = "image/jpeg"
            except (OSError, ValueError, Image.DecompressionBombError):
                form.errors["foto"] = "Envie uma foto PNG ou JPEG de até 512 KB e 16 megapixels."
    else:
        vehicle = form.relation("veiculo", "Veículo", Vehicle, kind != "gasto")
        driver = form.relation("motorista", "Motorista", Driver, kind == "multa")
        date_field = "ultima_troca" if kind == "oleo" else "data"
        posted = kind != "manutencao" or (existing and existing.status == "posted")
        record_date = form.date(date_field, "Data", past=bool(posted))
        if not posted and record_date and record_date < today() and (not existing or record_date != existing.date):
            form.errors[date_field] = "Agende para hoje ou uma data futura."
        raw_key = values.get("submission_key") or str(uuid.uuid4())
        try:
            key = str(uuid.UUID(raw_key))
        except ValueError:
            key = None
            form.errors["_form"] = "Atualize a página antes de tentar novamente."
        record = FleetRecord(kind=kind, date=record_date, vehicle_id=vehicle.id if vehicle else None,
                             driver_id=driver.id if driver else None, created_by=actor.id, submission_key=key,
                             status=existing.status if existing else ("scheduled" if kind == "manutencao" else "posted"))
        if kind == "combustivel":
            record.fuel_ml = form.number("litros", "Litros", scale=1000, minimum=0.001, maximum=1000)
            record.price_cents = form.number("valor_litro", "Preço por litro", scale=100, minimum=0.01, maximum=100)
            record.amount_cents = fuel_total(record.fuel_ml, record.price_cents) if record.fuel_ml and record.price_cents else 0
            record.description = form.text("posto", "posto", 120, False)
        else:
            record.amount_cents = form.number("valor", "Valor", scale=100, minimum=0.01, maximum=1_000_000)
            record.description = form.text("observacoes" if kind == "manutencao" else "descricao", "descrição", 1000, kind in ("multa", "gasto"))
        record.subtype = form.text("tipo", "tipo", 80, kind in ("multa", "gasto", "manutencao"))
        if kind in ("oleo", "combustivel"):
            record.odometer = form.number("quilometragem", "Quilometragem", maximum=9_999_999, required=kind == "oleo")
        if kind == "oleo":
            record.next_date = form.date("proxima_troca", "Próxima troca")
            record.next_odometer = form.number("proxima_quilometragem", "Próxima quilometragem", maximum=9_999_999)
            if record_date and record.next_date and record.next_date <= record_date:
                form.errors["proxima_troca"] = "A próxima troca deve ser posterior à última."
            if record.odometer is not None and record.next_odometer is not None and record.next_odometer <= record.odometer:
                form.errors["proxima_quilometragem"] = "A próxima quilometragem deve ser maior que a da troca."
        unchanged_reading = existing and all(getattr(record, key) == getattr(existing, key) for key in ("vehicle_id", "date", "odometer"))
        if vehicle and record.odometer is not None and record_date and not unchanged_reading:
            # Historical entries may be below today's reading, but never reverse
            # chronological readings or move an older reading beyond a newer one.
            before = FleetRecord.query.filter(FleetRecord.id != (existing.id if existing else None), FleetRecord.vehicle_id == vehicle.id, FleetRecord.date <= record_date,
                                               FleetRecord.odometer.isnot(None)).order_by(FleetRecord.date.desc(), FleetRecord.odometer.desc()).first()
            after = FleetRecord.query.filter(FleetRecord.id != (existing.id if existing else None), FleetRecord.vehicle_id == vehicle.id, FleetRecord.date > record_date,
                                              FleetRecord.odometer.isnot(None)).order_by(FleetRecord.date, FleetRecord.odometer).first()
            if (before and record.odometer < before.odometer) or (after and record.odometer > after.odometer):
                form.errors["quilometragem"] = "A quilometragem conflita com leituras já cadastradas."
            if record_date >= vehicle.reading_date and record.odometer < vehicle.odometer:
                form.errors["quilometragem"] = "A leitura atual não pode diminuir o odômetro."
            elif record_date < vehicle.reading_date and record.odometer > vehicle.odometer:
                form.errors["quilometragem"] = "Uma leitura anterior não pode superar o odômetro atual."
    return record, form.errors
