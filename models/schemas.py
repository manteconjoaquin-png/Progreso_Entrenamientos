from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class JiuJitsuMatchCreate(BaseModel):
    rival: str
    resultado: str


class JiuJitsuSessionCreate(BaseModel):
    fecha: date
    estado_fisico: str
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
    matches: list[JiuJitsuMatchResponse]

    class Config:
        from_attributes = True


class PadelSessionCreate(BaseModel):
    fecha: date
    tipo: Literal["Partido", "Entrenamiento"]
    compañero: str
    errores: int = Field(ge=0)
    resultado: str
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
    rivals: list[PadelRivalResponse]

    class Config:
        from_attributes = True


class TradingSessionCreate(BaseModel):
    fecha: date
    activo: str
    aprendizaje: str
    resultado: Decimal = Field(
        strict=True,
        max_digits=10,
        decimal_places=2,
    )

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

    class Config:
        from_attributes = True