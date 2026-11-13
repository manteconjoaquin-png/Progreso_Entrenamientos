import datetime
import json
from collections.abc import Generator
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from config.database import SessionLocal
from models.db_models import (
    JiuJitsuMatch,
    JiuJitsuSession,
    PadelRival,
    PadelSession,
    FutbolSession,
    TradingSession,
)
from models.schemas import (
    JiuJitsuMatchCreate,
    JiuJitsuSessionCreate,
    JiuJitsuSessionResponse,
    JiuJitsuSessionUpdate,
    FutbolCreate,
    FutbolResponse,
    PadelSessionCreate,
    PadelSessionResponse,
    PadelSessionUpdate,
    TradingSessionCreate,
    TradingSessionResponse,
    TradingSessionUpdate,
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
                rival_cinturon=match.rival_cinturon,
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


def _update_record(
    db: Session,
    record: Any,
    update_data: BaseModel,
    excluded_fields: set[str] | None = None,
) -> Any:
    updated_fields = update_data.model_dump(exclude_unset=True)
    for field_name, field_value in updated_fields.items():
        if excluded_fields is not None and field_name in excluded_fields:
            continue
        setattr(record, field_name, field_value)
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


def _futbol_response(record: FutbolSession) -> FutbolResponse:
    response_data = {
        column.name: getattr(record, column.name)
        for column in FutbolSession.__table__.columns
    }
    raw_positions = record.posiciones
    try:
        positions = json.loads(raw_positions) if raw_positions else []
    except (json.JSONDecodeError, TypeError):
        positions = []
    response_data["posiciones"] = positions if isinstance(positions, list) else []
    return FutbolResponse.model_validate(response_data)


def _serialize_futbol_records(records: list[FutbolSession]) -> list[dict[str, Any]]:
    serialized_records: list[dict[str, Any]] = []
    for record in records:
        response = _futbol_response(record)
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
        horario=session_data.horario,
        estado_fisico=session_data.estado_fisico,
        comentarios=session_data.comentarios,
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
        horario=session_data.horario,
        lado_juego=session_data.lado_juego,
        tipo=session_data.tipo,
        compañero=session_data.compañero,
        errores=session_data.errores,
        resultado=session_data.resultado,
        comentarios=session_data.comentarios,
        rivals=_build_padel_rivals(session_data.rivals),
    )
    saved_session = _save_record(db, db_session)
    return PadelSessionResponse.model_validate(saved_session)


@router.post("/futbol", response_model=FutbolResponse, status_code=201)
def create_futbol_session(
    session_data: FutbolCreate,
    db: Session = Depends(get_db),
) -> FutbolResponse:
    positions_json = json.dumps(
        [position.model_dump() for position in session_data.posiciones]
    )
    session_fields = session_data.model_dump(exclude={"posiciones"})
    db_session = FutbolSession(**session_fields, posiciones=positions_json)
    saved_session = _save_record(db, db_session)
    return _futbol_response(saved_session)


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
        comentarios=session_data.comentarios,
    )
    saved_session = _save_record(db, db_session)
    return TradingSessionResponse.model_validate(saved_session)


@router.put("/jiujitsu/{session_id}", response_model=JiuJitsuSessionResponse)
def update_jiujitsu_session(
    session_id: int,
    session_data: JiuJitsuSessionUpdate,
    db: Session = Depends(get_db),
) -> JiuJitsuSessionResponse:
    db_session = (
        db.query(JiuJitsuSession)
        .filter(JiuJitsuSession.id == session_id)
        .first()
    )
    if db_session is None:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    if "matches" in session_data.model_fields_set:
        db_session.matches = _build_jiujitsu_matches(session_data.matches or [])
    updated_session = _update_record(
        db,
        db_session,
        session_data,
        excluded_fields={"matches"},
    )
    return JiuJitsuSessionResponse.model_validate(updated_session)


@router.delete("/jiujitsu/{session_id}", status_code=204)
def delete_jiujitsu_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> None:
    session = (
        db.query(JiuJitsuSession)
        .filter(JiuJitsuSession.id == session_id)
        .first()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    db.delete(session)
    db.commit()


@router.put("/padel/{session_id}", response_model=PadelSessionResponse)
def update_padel_session(
    session_id: int,
    session_data: PadelSessionUpdate,
    db: Session = Depends(get_db),
) -> PadelSessionResponse:
    db_session = (
        db.query(PadelSession)
        .filter(PadelSession.id == session_id)
        .first()
    )
    if db_session is None:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    if "rivals" in session_data.model_fields_set:
        db_session.rivals = _build_padel_rivals(session_data.rivals or [])
    updated_session = _update_record(
        db,
        db_session,
        session_data,
        excluded_fields={"rivals"},
    )
    return PadelSessionResponse.model_validate(updated_session)


@router.delete("/padel/{session_id}", status_code=204)
def delete_padel_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> None:
    session = (
        db.query(PadelSession)
        .filter(PadelSession.id == session_id)
        .first()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    db.delete(session)
    db.commit()


@router.put("/futbol/{session_id}", response_model=FutbolResponse)
def update_futbol_session(
    session_id: int,
    session_data: FutbolCreate,
    db: Session = Depends(get_db),
) -> FutbolResponse:
    db_session = (
        db.query(FutbolSession)
        .filter(FutbolSession.id == session_id)
        .first()
    )
    if db_session is None:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    db_session.posiciones = json.dumps(
        [position.model_dump() for position in session_data.posiciones]
    )
    updated_session = _update_record(
        db,
        db_session,
        session_data,
        excluded_fields={"posiciones"},
    )
    return _futbol_response(updated_session)


@router.delete("/futbol/{session_id}", status_code=204)
def delete_futbol_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> None:
    session = (
        db.query(FutbolSession)
        .filter(FutbolSession.id == session_id)
        .first()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    db.delete(session)
    db.commit()


@router.put("/trading/{session_id}", response_model=TradingSessionResponse)
def update_trading_session(
    session_id: int,
    session_data: TradingSessionUpdate,
    db: Session = Depends(get_db),
) -> TradingSessionResponse:
    db_session = (
        db.query(TradingSession)
        .filter(TradingSession.id == session_id)
        .first()
    )
    if db_session is None:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    updated_session = _update_record(db, db_session, session_data)
    return TradingSessionResponse.model_validate(updated_session)


@router.delete("/trading/{session_id}", status_code=204)
def delete_trading_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> None:
    session = (
        db.query(TradingSession)
        .filter(TradingSession.id == session_id)
        .first()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    db.delete(session)
    db.commit()


@router.get("/history", response_model=dict[str, Any])
def get_history(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    current_year = datetime.date.today().year
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
    futbol_records: list[FutbolSession] = []
    futbol_serialized: list[dict[str, Any]] = []
    futbol_years: set[int] = set()
    futbol_win_rate = Decimal("0.0")
    try:
        futbol_records = (
            db.query(FutbolSession)
            .order_by(FutbolSession.fecha.desc())
            .all()
        )
        futbol_years = {session.fecha.year for session in futbol_records}
        if year is not None:
            futbol_records = [
                session for session in futbol_records if session.fecha.year == year
            ]
        futbol_serialized = _serialize_futbol_records(futbol_records)
        futbol_total = len(futbol_records)
        futbol_victories = sum(
            session.resultado == "Victoria" for session in futbol_records
        )
        if futbol_total > 0:
            futbol_win_rate = (
                Decimal(futbol_victories) / Decimal(futbol_total)
            ) * Decimal("100")
    except Exception as error:
        print(f"Error al consultar o procesar sesiones de Fútbol: {error}")
        db.rollback()
        futbol_records = []
        futbol_serialized = []
        futbol_years = set()
        futbol_win_rate = Decimal("0.0")

    trading_records = (
        db.query(TradingSession)
        .order_by(TradingSession.fecha.desc())
        .all()
    )
    jiujitsu_matches = (
        db.query(JiuJitsuMatch)
        .options(joinedload(JiuJitsuMatch.session))
        .all()
    )

    available_years_set: set[int] = set()
    for session in jiujitsu_records:
        available_years_set.add(session.fecha.year)
    for session in padel_records:
        available_years_set.add(session.fecha.year)
    available_years_set.update(futbol_years)
    for session in trading_records:
        available_years_set.add(session.fecha.year)
    available_years = sorted(available_years_set, reverse=True)

    metrics_year = current_year
    if year is not None:
        metrics_year = year
        filtered_jiujitsu_records: list[JiuJitsuSession] = []
        for session in jiujitsu_records:
            if session.fecha.year == year:
                filtered_jiujitsu_records.append(session)
        jiujitsu_records = filtered_jiujitsu_records

        filtered_padel_records: list[PadelSession] = []
        for session in padel_records:
            if session.fecha.year == year:
                filtered_padel_records.append(session)
        padel_records = filtered_padel_records

        filtered_trading_records: list[TradingSession] = []
        for session in trading_records:
            if session.fecha.year == year:
                filtered_trading_records.append(session)
        trading_records = filtered_trading_records

        filtered_jiujitsu_matches: list[JiuJitsuMatch] = []
        for match in jiujitsu_matches:
            if match.session.fecha.year == year:
                filtered_jiujitsu_matches.append(match)
        jiujitsu_matches = filtered_jiujitsu_matches

    horarios = ("Mañana", "Tarde", "Noche")
    cinturones = ("Blanco", "Azul", "Morado", "Marrón", "Negro")
    lados = ("Derecha", "Revés")

    jiujitsu_total = 0
    jiujitsu_victories = 0
    jiujitsu_year_total = 0
    jiujitsu_year_victories = 0
    jiujitsu_horarios_totales: dict[str, int] = {}
    jiujitsu_horarios_victorias: dict[str, int] = {}
    for horario in horarios:
        jiujitsu_horarios_totales[horario] = 0
        jiujitsu_horarios_victorias[horario] = 0

    jiujitsu_cinturon_totales: dict[str, int] = {}
    jiujitsu_cinturon_victorias: dict[str, int] = {}
    jiujitsu_cinturon_horario_totales: dict[str, int] = {}
    jiujitsu_cinturon_horario_victorias: dict[str, int] = {}
    for cinturon in cinturones:
        jiujitsu_cinturon_totales[cinturon] = 0
        jiujitsu_cinturon_victorias[cinturon] = 0
        for horario in horarios:
            cruce = f"{cinturon}_{horario}"
            jiujitsu_cinturon_horario_totales[cruce] = 0
            jiujitsu_cinturon_horario_victorias[cruce] = 0

    for match in jiujitsu_matches:
        jiujitsu_total += 1
        if match.resultado == "Victoria":
            jiujitsu_victories += 1
        if match.session.fecha.year == metrics_year:
            jiujitsu_year_total += 1
            if match.resultado == "Victoria":
                jiujitsu_year_victories += 1

        horario = match.session.horario
        cinturon = match.rival_cinturon
        if horario in jiujitsu_horarios_totales:
            jiujitsu_horarios_totales[horario] += 1
            if match.resultado == "Victoria":
                jiujitsu_horarios_victorias[horario] += 1

        if cinturon in jiujitsu_cinturon_totales:
            jiujitsu_cinturon_totales[cinturon] += 1
            if match.resultado == "Victoria":
                jiujitsu_cinturon_victorias[cinturon] += 1

            if horario in horarios:
                cruce = f"{cinturon}_{horario}"
                jiujitsu_cinturon_horario_totales[cruce] += 1
                if match.resultado == "Victoria":
                    jiujitsu_cinturon_horario_victorias[cruce] += 1

    padel_total = 0
    padel_victories = 0
    padel_year_total = 0
    padel_year_victories = 0
    padel_horarios_totales: dict[str, int] = {}
    padel_horarios_victorias: dict[str, int] = {}
    for horario in horarios:
        padel_horarios_totales[horario] = 0
        padel_horarios_victorias[horario] = 0

    padel_lado_totales: dict[str, int] = {}
    padel_lado_victorias: dict[str, int] = {}
    padel_lado_horario_totales: dict[str, int] = {}
    padel_lado_horario_victorias: dict[str, int] = {}
    for lado in lados:
        padel_lado_totales[lado] = 0
        padel_lado_victorias[lado] = 0
        for horario in horarios:
            cruce = f"{lado}_{horario}"
            padel_lado_horario_totales[cruce] = 0
            padel_lado_horario_victorias[cruce] = 0

    for session in padel_records:
        padel_total += 1
        if session.resultado == "Victoria":
            padel_victories += 1
        if session.fecha.year == metrics_year:
            padel_year_total += 1
            if session.resultado == "Victoria":
                padel_year_victories += 1

        horario = session.horario
        lado = session.lado_juego
        if horario in padel_horarios_totales:
            padel_horarios_totales[horario] += 1
            if session.resultado == "Victoria":
                padel_horarios_victorias[horario] += 1

        if lado in padel_lado_totales:
            padel_lado_totales[lado] += 1
            if session.resultado == "Victoria":
                padel_lado_victorias[lado] += 1

            if horario in horarios:
                cruce = f"{lado}_{horario}"
                padel_lado_horario_totales[cruce] += 1
                if session.resultado == "Victoria":
                    padel_lado_horario_victorias[cruce] += 1

    trading_total = 0
    trading_wins = 0
    trading_year_total = 0
    trading_year_wins = 0
    trading_net_profit = Decimal("0.00")
    for session in trading_records:
        trading_total += 1
        trading_net_profit += session.resultado
        if session.resultado > 0:
            trading_wins += 1
        if session.fecha.year == metrics_year:
            trading_year_total += 1
            if session.resultado > 0:
                trading_year_wins += 1

    jiujitsu_horarios: dict[str, Decimal] = {}
    padel_horarios: dict[str, Decimal] = {}
    for horario in horarios:
        jiujitsu_horario_win_rate = Decimal("0.0")
        if jiujitsu_horarios_totales[horario] > 0:
            jiujitsu_horario_win_rate = (
                Decimal(jiujitsu_horarios_victorias[horario])
                / Decimal(jiujitsu_horarios_totales[horario])
            ) * Decimal("100")
        jiujitsu_horarios[horario] = jiujitsu_horario_win_rate

        padel_horario_win_rate = Decimal("0.0")
        if padel_horarios_totales[horario] > 0:
            padel_horario_win_rate = (
                Decimal(padel_horarios_victorias[horario])
                / Decimal(padel_horarios_totales[horario])
            ) * Decimal("100")
        padel_horarios[horario] = padel_horario_win_rate

    win_rate_cinturon: dict[str, Decimal] = {}
    for cinturon in cinturones:
        win_rate = Decimal("0.0")
        if jiujitsu_cinturon_totales[cinturon] > 0:
            win_rate = (
                Decimal(jiujitsu_cinturon_victorias[cinturon])
                / Decimal(jiujitsu_cinturon_totales[cinturon])
            ) * Decimal("100")
        win_rate_cinturon[cinturon] = win_rate

    win_rate_cinturon_horario: dict[str, Decimal] = {}
    for cinturon in cinturones:
        for horario in horarios:
            cruce = f"{cinturon}_{horario}"
            win_rate = Decimal("0.0")
            if jiujitsu_cinturon_horario_totales[cruce] > 0:
                win_rate = (
                    Decimal(jiujitsu_cinturon_horario_victorias[cruce])
                    / Decimal(jiujitsu_cinturon_horario_totales[cruce])
                ) * Decimal("100")
            win_rate_cinturon_horario[cruce] = win_rate

    win_rate_lado: dict[str, Decimal] = {}
    for lado in lados:
        win_rate = Decimal("0.0")
        if padel_lado_totales[lado] > 0:
            win_rate = (
                Decimal(padel_lado_victorias[lado])
                / Decimal(padel_lado_totales[lado])
            ) * Decimal("100")
        win_rate_lado[lado] = win_rate

    win_rate_lado_horario: dict[str, Decimal] = {}
    for lado in lados:
        for horario in horarios:
            cruce = f"{lado}_{horario}"
            win_rate = Decimal("0.0")
            if padel_lado_horario_totales[cruce] > 0:
                win_rate = (
                    Decimal(padel_lado_horario_victorias[cruce])
                    / Decimal(padel_lado_horario_totales[cruce])
                ) * Decimal("100")
            win_rate_lado_horario[cruce] = win_rate

    jiujitsu_win_rate = Decimal("0.0")
    if jiujitsu_total > 0:
        jiujitsu_win_rate = (
            Decimal(jiujitsu_victories) / Decimal(jiujitsu_total)
        ) * Decimal("100")

    padel_win_rate = Decimal("0.0")
    if padel_total > 0:
        padel_win_rate = (
            Decimal(padel_victories) / Decimal(padel_total)
        ) * Decimal("100")

    trading_win_rate = Decimal("0.0")
    if trading_total > 0:
        trading_win_rate = (
            Decimal(trading_wins) / Decimal(trading_total) * Decimal("100")
        ).quantize(Decimal("0.01"))

    jiujitsu_year_win_rate = Decimal("0.0")
    if jiujitsu_year_total > 0:
        jiujitsu_year_win_rate = (
            Decimal(jiujitsu_year_victories)
            / Decimal(jiujitsu_year_total)
        ) * Decimal("100")

    padel_win_rate_year = Decimal("0.0")
    if padel_year_total > 0:
        padel_win_rate_year = (
            Decimal(padel_year_victories) / Decimal(padel_year_total)
        ) * Decimal("100")

    trading_win_rate_year = Decimal("0.0")
    if trading_year_total > 0:
        trading_win_rate_year = (
            Decimal(trading_year_wins)
            / Decimal(trading_year_total)
            * Decimal("100")
        ).quantize(Decimal("0.01"))

    return {
        "available_years": available_years,
        "jiujitsu": _serialize_records(jiujitsu_records, JiuJitsuSessionResponse),
        "padel": _serialize_records(padel_records, PadelSessionResponse),
        "futbol": futbol_serialized,
        "trading": _serialize_records(trading_records, TradingSessionResponse),
        "metrics": {
            "jiujitsu_win_rate": jiujitsu_win_rate,
            "padel_win_rate": padel_win_rate,
            "futbol_win_rate": futbol_win_rate,
            "jiujitsu_year_win_rate": jiujitsu_year_win_rate,
            "padel_win_rate_year": padel_win_rate_year,
            "jiujitsu_horarios": jiujitsu_horarios,
            "padel_horarios": padel_horarios,
            "win_rate_cinturon": win_rate_cinturon,
            "win_rate_cinturon_horario": win_rate_cinturon_horario,
            "win_rate_lado": win_rate_lado,
            "win_rate_lado_horario": win_rate_lado_horario,
            "trading_win_rate": trading_win_rate,
            "trading_win_rate_year": trading_win_rate_year,
            "trading_net_profit": trading_net_profit,
        },
    }