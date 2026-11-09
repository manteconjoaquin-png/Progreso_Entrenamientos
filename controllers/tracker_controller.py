from collections.abc import Generator
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config.database import SessionLocal
from models.db_models import (
    JiuJitsuMatch,
    JiuJitsuSession,
    PadelRival,
    PadelSession,
    TradingSession,
)
from models.schemas import (
    JiuJitsuMatchCreate,
    JiuJitsuSessionCreate,
    JiuJitsuSessionResponse,
    PadelSessionCreate,
    PadelSessionResponse,
    TradingSessionCreate,
    TradingSessionResponse,
)


router = APIRouter(prefix="/api/tracker", tags=["Tracker"])


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _build_jiujitsu_matches(
    matches: list[JiuJitsuMatchCreate],
) -> list[JiuJitsuMatch]:
    db_matches: list[JiuJitsuMatch] = []
    for match in matches:
        db_matches.append(
            JiuJitsuMatch(
                rival=match.rival,
                resultado=match.resultado,
            )
        )
    return db_matches


def _build_padel_rivals(rival_names: list[str]) -> list[PadelRival]:
    db_rivals: list[PadelRival] = []
    for rival_name in rival_names:
        db_rivals.append(PadelRival(rival_name=rival_name))
    return db_rivals


def _save_record(db: Session, record: Any) -> Any:
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _serialize_records(
    records: list[Any],
    schema: type[BaseModel],
) -> list[dict[str, Any]]:
    serialized_records: list[dict[str, Any]] = []
    for record in records:
        response = schema.model_validate(record)
        serialized_records.append(response.model_dump(mode="json"))
    return serialized_records


@router.post(
    "/jiujitsu",
    response_model=JiuJitsuSessionResponse,
    status_code=201,
)
def create_jiujitsu_session(
    session_data: JiuJitsuSessionCreate,
    db: Session = Depends(get_db),
) -> JiuJitsuSessionResponse:
    db_session = JiuJitsuSession(
        fecha=session_data.fecha,
        estado_fisico=session_data.estado_fisico,
        matches=_build_jiujitsu_matches(session_data.matches),
    )
    saved_session = _save_record(db, db_session)
    return JiuJitsuSessionResponse.model_validate(saved_session)


@router.post(
    "/padel",
    response_model=PadelSessionResponse,
    status_code=201,
)
def create_padel_session(
    session_data: PadelSessionCreate,
    db: Session = Depends(get_db),
) -> PadelSessionResponse:
    db_session = PadelSession(
        fecha=session_data.fecha,
        tipo=session_data.tipo,
        compañero=session_data.compañero,
        errores=session_data.errores,
        resultado=session_data.resultado,
        rivals=_build_padel_rivals(session_data.rivals),
    )
    saved_session = _save_record(db, db_session)
    return PadelSessionResponse.model_validate(saved_session)


@router.post(
    "/trading",
    response_model=TradingSessionResponse,
    status_code=201,
)
def create_trading_session(
    session_data: TradingSessionCreate,
    db: Session = Depends(get_db),
) -> TradingSessionResponse:
    db_session = TradingSession(
        fecha=session_data.fecha,
        activo=session_data.activo,
        aprendizaje=session_data.aprendizaje,
        resultado=session_data.resultado,
    )
    saved_session = _save_record(db, db_session)
    return TradingSessionResponse.model_validate(saved_session)


@router.get("/history", response_model=dict[str, list[dict[str, Any]]])
def get_history(db: Session = Depends(get_db)) -> dict[str, list[dict[str, Any]]]:
    jiujitsu_records = (
        db.query(JiuJitsuSession)
        .order_by(JiuJitsuSession.fecha.desc())
        .all()
    )
    padel_records = (
        db.query(PadelSession)
        .order_by(PadelSession.fecha.desc())
        .all()
    )
    trading_records = (
        db.query(TradingSession)
        .order_by(TradingSession.fecha.desc())
        .all()
    )

    return {
        "jiujitsu": _serialize_records(jiujitsu_records, JiuJitsuSessionResponse),
        "padel": _serialize_records(padel_records, PadelSessionResponse),
        "trading": _serialize_records(trading_records, TradingSessionResponse),
    }