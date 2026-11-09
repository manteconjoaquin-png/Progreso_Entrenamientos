from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class JiuJitsuMatchCreate(BaseModel):
    rival: str
    resultado: str


class JiuJitsuSessionCreate(BaseModel):
    fecha: date
    estado_fisico: str
    comentarios: Optional[str] = None
    matches: list[JiuJitsuMatchCreate] = Field(default_factory=list)


class JiuJitsuMatchResponse(BaseModel):
    id: int
    session_id: int
    rival: str
    resultado: str

    class Config:
        from_attributes = True


class JiuJitsuSessionResponse(BaseModel):
    id: int
    fecha: date
    estado_fisico: str
    comentarios: Optional[str] = None
    matches: list[JiuJitsuMatchResponse]

    class Config:
        from_attributes = True


class JiuJitsuSessionUpdate(BaseModel):
    fecha: Optional[date] = None
    estado_fisico: Optional[str] = None
    comentarios: Optional[str] = None
    matches: Optional[list[JiuJitsuMatchCreate]] = None


class PadelSessionCreate(BaseModel):
    fecha: date
    tipo: Literal["Partido", "Entrenamiento"]
    compañero: str
    errores: int = Field(ge=0)
    resultado: str
    comentarios: Optional[str] = None
    rivals: list[str] = Field(default_factory=list)


class PadelRivalResponse(BaseModel):
    id: int
    padel_id: int
    rival_name: str

    class Config:
        from_attributes = True


class PadelSessionResponse(BaseModel):
    id: int
    fecha: date
    tipo: Literal["Partido", "Entrenamiento"]
    compañero: str
    errores: int
    resultado: str
    comentarios: Optional[str] = None
    rivals: list[PadelRivalResponse]

    class Config:
        from_attributes = True


class PadelSessionUpdate(BaseModel):
    fecha: Optional[date] = None
    tipo: Optional[Literal["Partido", "Entrenamiento"]] = None
    compañero: Optional[str] = None
    errores: Optional[int] = Field(default=None, ge=0)
    resultado: Optional[str] = None
    comentarios: Optional[str] = None
    rivals: Optional[list[str]] = None


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