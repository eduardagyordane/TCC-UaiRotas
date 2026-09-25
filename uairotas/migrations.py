"""Versioned, additive SQLite migrations. Run `flask init-db` after upgrading."""
from sqlalchemy import inspect, text

from .extensions import db
from .models import SchemaMigration


def migrate():
    inspector = inspect(db.engine)
    if "users" in inspector.get_table_names():
        columns = {c["name"] for c in inspector.get_columns("users")}
        additions = {"phone": "VARCHAR(20)", "address": "VARCHAR(255)", "cpf": "VARCHAR(11)",
                     "birth_date": "DATE", "auth_version": "INTEGER NOT NULL DEFAULT 1"}
        with db.engine.begin() as connection:
            for name, sql_type in additions.items():
                if name not in columns:
                    connection.execute(text(f"ALTER TABLE users ADD COLUMN {name} {sql_type}"))
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_cpf ON users(cpf)"))
    db.create_all()
    # The database guard also covers concurrent requests and direct SQL updates.
    if db.engine.dialect.name == "sqlite":
        with db.engine.begin() as connection:
            connection.execute(text("""
                CREATE TRIGGER IF NOT EXISTS protect_last_admin_update
                BEFORE UPDATE OF role, active ON users
                WHEN OLD.role = 'admin' AND OLD.active = 1
                  AND (NEW.role != 'admin' OR NEW.active != 1)
                  AND (SELECT count(*) FROM users WHERE role = 'admin' AND active = 1) <= 1
                BEGIN SELECT RAISE(ABORT, 'last_active_admin'); END
            """))
            connection.execute(text("""
                CREATE TRIGGER IF NOT EXISTS protect_last_admin_delete
                BEFORE DELETE ON users
                WHEN OLD.role = 'admin' AND OLD.active = 1
                  AND (SELECT count(*) FROM users WHERE role = 'admin' AND active = 1) <= 1
                BEGIN SELECT RAISE(ABORT, 'last_active_admin'); END
            """))
    if db.session.get(SchemaMigration, 1) is None:
        db.session.add(SchemaMigration(version=1))
        db.session.commit()
    # Orders need their historical vehicle, not the driver's current assignment.
    columns = {column["name"] for column in inspect(db.engine).get_columns("service_orders")}
    with db.engine.begin() as connection:
        if "vehicle_id" not in columns:
            connection.execute(text("ALTER TABLE service_orders ADD COLUMN vehicle_id INTEGER REFERENCES vehicles(id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_service_orders_vehicle_id ON service_orders(vehicle_id)"))
    if db.session.get(SchemaMigration, 2) is None:
        # Only enrich our synthetic examples when their day has one unique link.
        # Real records without a historical link remain unassigned.
        db.session.execute(text("""
            UPDATE service_orders SET vehicle_id = (
                SELECT min(t.vehicle_id) FROM trips t
                WHERE t.driver_id = service_orders.driver_id AND t.date = service_orders.date AND t.source = 'demo'
            )
            WHERE source = 'demo' AND vehicle_id IS NULL AND (
                SELECT count(DISTINCT t.vehicle_id) FROM trips t
                WHERE t.driver_id = service_orders.driver_id AND t.date = service_orders.date AND t.source = 'demo'
            ) = 1
        """))
        db.session.execute(text("""
            UPDATE fleet_records SET driver_id = (
                SELECT min(t.driver_id) FROM trips t
                WHERE t.vehicle_id = fleet_records.vehicle_id AND t.date = fleet_records.date AND t.source = 'demo'
            )
            WHERE source = 'demo' AND driver_id IS NULL AND (
                SELECT count(DISTINCT t.driver_id) FROM trips t
                WHERE t.vehicle_id = fleet_records.vehicle_id AND t.date = fleet_records.date AND t.source = 'demo'
            ) = 1
        """))
        db.session.add(SchemaMigration(version=2))
        db.session.commit()
