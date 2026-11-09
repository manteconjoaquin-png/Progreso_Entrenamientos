from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import models.db_models
from config.database import Base, engine
from controllers.tracker_controller import router


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Tracker Multidisciplinar de Progreso")
app.include_router(router)
app.mount("/views", StaticFiles(directory="views"), name="views")


@app.get("/", response_class=FileResponse)
def read_dashboard() -> FileResponse:
    return FileResponse("views/dashboard.html")