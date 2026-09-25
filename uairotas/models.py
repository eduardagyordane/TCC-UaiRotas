from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    address = db.Column(db.String(255), nullable=True)
    cpf = db.Column(db.String(11), unique=True, nullable=True, index=True)
    birth_date = db.Column(db.Date, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="admin")
    active = db.Column(db.Boolean, nullable=False, default=True)
    auth_version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    @property
    def is_active(self):
        return self.active

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        # Changing this version revokes both sessions and remember-me cookies.
        return f"{self.id}:{self.auth_version}"


class Driver(db.Model):
    __tablename__ = "drivers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    license_number = db.Column(db.String(11), unique=True, nullable=False)
    category = db.Column(db.String(2))
    first_license = db.Column(db.Date)
    license_expiry = db.Column(db.Date)
    registration = db.Column(db.String(60))
    identifier = db.Column(db.String(30))
    photo = db.Column(db.LargeBinary)
    photo_mime = db.Column(db.String(30))
    source = db.Column(db.String(20), nullable=False, default="manual")


class Vehicle(db.Model):
    __tablename__ = "vehicles"
    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(17), nullable=False, unique=True)
    nickname = db.Column(db.String(80), nullable=False)
    brand = db.Column(db.String(60), nullable=False)
    model = db.Column(db.String(80), nullable=False)
    year = db.Column(db.Integer)
    group = db.Column(db.String(80))
    size = db.Column(db.String(20))
    map_type = db.Column(db.String(20))
    tag = db.Column(db.String(80))
    odometer = db.Column(db.Integer, nullable=False, default=0)
    reading_date = db.Column(db.Date, nullable=False)
    reading_time = db.Column(db.Time)
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), index=True)
    driver = db.relationship(Driver, lazy="joined")
    source = db.Column(db.String(20), nullable=False, default="manual")
    __table_args__ = (db.CheckConstraint("odometer >= 0", name="vehicle_odometer_positive"),)


class FleetRecord(db.Model):
    """Money is integer cents; fuel quantities are integer millilitres."""
    __tablename__ = "fleet_records"
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(20), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), index=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"))
    vehicle = db.relationship(Vehicle, lazy="joined")
    driver = db.relationship(Driver, lazy="joined")
    amount_cents = db.Column(db.Integer, nullable=False)
    fuel_ml = db.Column(db.Integer)
    price_cents = db.Column(db.Integer)
    odometer = db.Column(db.Integer)
    next_date = db.Column(db.Date)
    next_odometer = db.Column(db.Integer)
    description = db.Column(db.String(1000), nullable=False, default="")
    subtype = db.Column(db.String(80), nullable=False, default="")
    status = db.Column(db.String(20), nullable=False, default="posted")
    source = db.Column(db.String(20), nullable=False, default="manual")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    submission_key = db.Column(db.String(36), unique=True)
    __table_args__ = (
        db.CheckConstraint("amount_cents >= 0", name="record_amount_positive"),
        db.CheckConstraint("fuel_ml IS NULL OR fuel_ml > 0", name="record_fuel_positive"),
        db.Index("ix_fleet_period_status", "status", "date", "kind"),
    )


class Trip(db.Model):
    __tablename__ = "trips"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), nullable=False)
    vehicle = db.relationship(Vehicle, lazy="joined")
    driver = db.relationship(Driver, lazy="joined")
    distance_m = db.Column(db.Integer, nullable=False, default=0)
    transit_minutes = db.Column(db.Integer, nullable=False, default=0)
    lunch_minutes = db.Column(db.Integer, nullable=False, default=0)
    deviations = db.Column(db.Integer, nullable=False, default=0)
    points = db.Column(db.JSON, nullable=False, default=list)
    # planned paths must never be described as observed telemetry.
    path_kind = db.Column(db.String(20), nullable=False, default="planned")
    source = db.Column(db.String(20), nullable=False, default="manual")
    __table_args__ = (db.Index("ix_trip_driver_date", "driver_id", "date"),)


class ServiceOrder(db.Model):
    __tablename__ = "service_orders"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), nullable=False, unique=True)
    date = db.Column(db.Date, nullable=False, index=True)
    time = db.Column(db.String(5), nullable=False)
    customer = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    service = db.Column(db.String(120), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), nullable=False)
    driver = db.relationship(Driver, lazy="joined")
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), index=True)
    vehicle = db.relationship(Vehicle, lazy="joined")
    status = db.Column(db.String(20), nullable=False)
    service_minutes = db.Column(db.Integer, nullable=False, default=0)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    source = db.Column(db.String(20), nullable=False, default="manual")
    __table_args__ = (db.Index("ix_order_date_status", "date", "status", "driver_id"),)


class Place(db.Model):
    __tablename__ = "places"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(30), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(20), nullable=False, default="manual")


class AlertAcknowledgement(db.Model):
    __tablename__ = "alert_acknowledgements"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    occurrence_id = db.Column(db.String(120), primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class AuditLog(db.Model):
    __tablename__ = "audit_log"
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(80), nullable=False)
    entity = db.Column(db.String(30), nullable=False)
    entity_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)


class LoginAttempt(db.Model):
    __tablename__ = "login_attempts"
    id = db.Column(db.Integer, primary_key=True)
    bucket = db.Column(db.String(64), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)


class SchemaMigration(db.Model):
    __tablename__ = "schema_migrations"
    version = db.Column(db.Integer, primary_key=True)
    applied_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
