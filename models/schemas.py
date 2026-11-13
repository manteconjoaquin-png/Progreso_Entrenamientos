from datetime import date
from decimal import Decimal, InvalidOperation
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _validate_horario(value: object) -> str:
    if not isinstance(value, str) or value not in {"Mañana", "Tarde", "Noche"}:
        raise ValueError("horario debe ser 'Mañana', 'Tarde' o 'Noche'")
    return value


def _validate_rival_cinturon(value: object) -> str:
    valid_belts = {"Blanco", "Azul", "Morado", "Marrón", "Negro"}
    if not isinstance(value, str) or value not in valid_belts:
        raise ValueError(
            "rival_cinturon debe ser 'Blanco', 'Azul', 'Morado', 'Marrón' o 'Negro'"
        )
    return value


def _validate_lado_juego(value: object) -> str:
    if not isinstance(value, str) or value not in {"Derecha", "Revés"}:
        raise ValueError("lado_juego debe ser 'Derecha' o 'Revés'")
    return value


class JiuJitsuMatchCreate(BaseModel):
    rival: str
    rival_cinturon: str = "Blanco"
    resultado: str

    @field_validator("rival_cinturon", mode="before")
    @classmethod
    def validate_rival_cinturon(cls, value: object) -> str:
        return _validate_rival_cinturon(value)


class JiuJitsuSessionCreate(BaseModel):
    fecha: date
    horario: str
    estado_fisico: str
    comentarios: Optional[str] = None
    matches: list[JiuJitsuMatchCreate] = Field(default_factory=list)

    @field_validator("horario", mode="before")
    @classmethod
    def validate_horario(cls, value: object) -> str:
        return _validate_horario(value)


class JiuJitsuMatchResponse(BaseModel):
    id: int
    session_id: int
    rival: str
    rival_cinturon: str
    resultado: str

    @field_validator("rival_cinturon", mode="before")
    @classmethod
    def validate_rival_cinturon(cls, value: object) -> str:
        return _validate_rival_cinturon(value)

    class Config:
        from_attributes = True


class JiuJitsuSessionResponse(BaseModel):
    id: int
    fecha: date
    horario: str
    estado_fisico: str
    comentarios: Optional[str] = None
    matches: list[JiuJitsuMatchResponse]

    class Config:
        from_attributes = True


class JiuJitsuSessionUpdate(BaseModel):
    fecha: Optional[date] = None
    horario: str
    estado_fisico: Optional[str] = None
    comentarios: Optional[str] = None
    matches: Optional[list[JiuJitsuMatchCreate]] = None

    @field_validator("horario", mode="before")
    @classmethod
    def validate_horario(cls, value: object) -> str:
        return _validate_horario(value)


class PadelSessionCreate(BaseModel):
    fecha: date
    horario: str
    lado_juego: str = "Derecha"
    tipo: Literal["Partido", "Entrenamiento"]
    compañero: str
    errores: int = Field(ge=0)
    resultado: str
    comentarios: Optional[str] = None
    rivals: list[str] = Field(default_factory=list)

    @field_validator("horario", mode="before")
    @classmethod
    def validate_horario(cls, value: object) -> str:
        return _validate_horario(value)

    @field_validator("lado_juego", mode="before")
    @classmethod
    def validate_lado_juego(cls, value: object) -> str:
        return _validate_lado_juego(value)


class PadelRivalResponse(BaseModel):
    id: int
    padel_id: int
    rival_name: str

    class Config:
        from_attributes = True


class PadelSessionResponse(BaseModel):
    id: int
    fecha: date
    horario: str
    lado_juego: str
    tipo: Literal["Partido", "Entrenamiento"]
    compañero: str
    errores: int
    resultado: str
    comentarios: Optional[str] = None
    rivals: list[PadelRivalResponse]

    @field_validator("lado_juego", mode="before")
    @classmethod
    def validate_lado_juego(cls, value: object) -> str:
        return _validate_lado_juego(value)

    class Config:
        from_attributes = True


class PadelSessionUpdate(BaseModel):
    fecha: Optional[date] = None
    horario: str
    lado_juego: Optional[str] = None
    tipo: Optional[Literal["Partido", "Entrenamiento"]] = None
    compañero: Optional[str] = None
    errores: Optional[int] = Field(default=None, ge=0)
    resultado: Optional[str] = None
    comentarios: Optional[str] = None
    rivals: Optional[list[str]] = None

    @field_validator("horario", mode="before")
    @classmethod
    def validate_horario(cls, value: object) -> str:
        return _validate_horario(value)

    @field_validator("lado_juego", mode="before")
    @classmethod
    def validate_lado_juego(cls, value: object) -> str:
        return _validate_lado_juego(value)


class TradingSessionCreate(BaseModel):
    fecha: date
    activo: str
    aprendizaje: str
    resultado: Decimal = Field(
        strict=True,
        max_digits=10,
        decimal_places=2,
    )
    comentarios: Optional[str] = None

    @field_validator("resultado", mode="before")
    @classmethod
    def parse_resultado(cls, value: object) -> object:
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value))
        except InvalidOperation as error:
            raise ValueError("resultado debe ser un valor decimal válido") from error


class TradingSessionResponse(BaseModel):
    id: int
    fecha: date
    activo: str
    aprendizaje: str
    resultado: Decimal
    comentarios: Optional[str] = None

    class Config:
        from_attributes = True


class TradingSessionUpdate(BaseModel):
    fecha: Optional[date] = None
    activo: Optional[str] = None
    aprendizaje: Optional[str] = None
    resultado: Optional[Decimal] = Field(
        default=None,
        strict=True,
        max_digits=10,
        decimal_places=2,
    )
    comentarios: Optional[str] = None

    @field_validator("resultado", mode="before")
    @classmethod
    def parse_resultado(cls, value: object) -> object:
        if value is None or isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value))
        except InvalidOperation as error:
            raise ValueError("resultado debe ser un valor decimal válido") from error


class PosicionMinutos(BaseModel):
    posicion: Literal[
        "Portero",
        "Defensa",
        "Mediocentro",
        "Volante ofensivo",
        "Delantero",
    ]
    minutos: int = Field(ge=1, le=90)


class FutbolCreate(BaseModel):
    fecha: date
    formato: Literal["5", "7", "11"]
    tipo: Literal["Amistoso", "Competicion"]
    equipo: str = Field(min_length=1)
    tiempo_juego: int = Field(ge=5, le=90)
    goles_marcados: int = Field(ge=0, le=5)
    errores_cometidos: int = Field(ge=0)
    resultado: Literal["Victoria", "Derrota", "Empate"]
    estado_fisico: Literal["Muy cansado", "Cansado", "Normal", "Bien", "Genial"]
    comentarios: Optional[str] = None
    posiciones: List[PosicionMinutos] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_posiciones_minutes(self) -> "FutbolCreate":
        total_minutes = sum(position.minutos for position in self.posiciones)
        if total_minutes > self.tiempo_juego:
            raise ValueError(
                "La suma de los minutos por posición no puede superar el tiempo de juego"
            )
        return self


class FutbolResponse(FutbolCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)