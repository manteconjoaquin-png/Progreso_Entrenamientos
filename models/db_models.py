from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base


class JiuJitsuSession(Base):
    __tablename__ = "jiu_jitsu_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    estado_fisico: Mapped[str] = mapped_column(String, nullable=False)
    comentarios: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    matches: Mapped[list["JiuJitsuMatch"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class JiuJitsuMatch(Base):
    __tablename__ = "jiu_jitsu_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("jiu_jitsu_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    rival: Mapped[str] = mapped_column(String, nullable=False)
    resultado: Mapped[str] = mapped_column(String, nullable=False)

    session: Mapped[JiuJitsuSession] = relationship(back_populates="matches")


class PadelSession(Base):
    __tablename__ = "padel_sessions"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('Partido', 'Entrenamiento')",
            name="ck_padel_sessions_tipo",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    compañero: Mapped[str] = mapped_column(String, nullable=False)
    errores: Mapped[int] = mapped_column(Integer, nullable=False)
    resultado: Mapped[str] = mapped_column(String, nullable=False)
    comentarios: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    rivals: Mapped[list["PadelRival"]] = relationship(
        back_populates="padel_session",
        cascade="all, delete-orphan",
    )


class PadelRival(Base):
    __tablename__ = "padel_rivals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    padel_id: Mapped[int] = mapped_column(
        ForeignKey("padel_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    rival_name: Mapped[str] = mapped_column(String, nullable=False)

    padel_session: Mapped[PadelSession] = relationship(back_populates="rivals")


class TradingSession(Base):
    __tablename__ = "trading_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    activo: Mapped[str] = mapped_column(String, nullable=False)
    resultado: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    aprendizaje: Mapped[str] = mapped_column(String, nullable=False)
    comentarios: Mapped[Optional[str]] = mapped_column(String, nullable=True)