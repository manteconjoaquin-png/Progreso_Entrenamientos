from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

import models.db_models
from config.database import Base, engine
from controllers.tracker_controller import router


Base.metadata.create_all(bind=engine)


def migrate_horario_columns() -> None:
    with engine.begin() as connection:
        for table_name in ("jiu_jitsu_sessions", "padel_sessions"):
            column_names = {
                column["name"]
                for column in inspect(connection).get_columns(table_name)
            }
            if "horario" not in column_names:
                connection.execute(
                    text(
                        f"ALTER TABLE {table_name} "
                        "ADD COLUMN horario VARCHAR NOT NULL DEFAULT 'Tarde'"
                    )
                )


def migrate_activity_detail_columns() -> None:
    columns_to_add = (
        ("jiu_jitsu_matches", "rival_cinturon", "Blanco"),
        ("padel_sessions", "lado_juego", "Derecha"),
    )
    with engine.begin() as connection:
        for table_name, column_name, default_value in columns_to_add:
            column_names = {
                column["name"]
                for column in inspect(connection).get_columns(table_name)
            }
            if column_name not in column_names:
                connection.execute(
                    text(
                        f"ALTER TABLE {table_name} "
                        f"ADD COLUMN {column_name} VARCHAR NOT NULL "
                        f"DEFAULT '{default_value}'"
                    )
                )


def migrate_futbol_positions_column() -> None:
    table_name = "futbol_sessions"
    with engine.begin() as connection:
        inspector = inspect(connection)
        if not inspector.has_table(table_name):
            return
        column_names = {
            column["name"] for column in inspector.get_columns(table_name)
        }
        if "posiciones" not in column_names:
            connection.execute(
                text(
                    "ALTER TABLE futbol_sessions "
                    "ADD COLUMN posiciones TEXT NOT NULL DEFAULT '[]'"
                )
            )


migrate_horario_columns()
migrate_activity_detail_columns()
migrate_futbol_positions_column()

app = FastAPI(title="Tracker Multidisciplinar de Progreso")
app.include_router(router)
app.mount("/views", StaticFiles(directory="views"), name="views")


@app.get("/", response_class=FileResponse)
def read_dashboard() -> FileResponse:
    return FileResponse("views/dashboard.html")