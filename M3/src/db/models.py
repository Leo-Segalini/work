"""Modèles SQLAlchemy DiagOps — brief online M3."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base déclarative commune."""


class Equipment(Base):
    __tablename__ = "equipment"

    equipment_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    equipment_type: Mapped[str] = mapped_column(String(64), nullable=False)
    site_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    commissioning_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    criticality: Mapped[str] = mapped_column(String(16), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rated_power_kw: Mapped[float | None] = mapped_column(Float, nullable=True)

    events: Mapped[list[Event]] = relationship(back_populates="equipment")
    maintenance_records: Mapped[list[Maintenance]] = relationship(back_populates="equipment")
    sensor_readings: Mapped[list[SensorReading]] = relationship(back_populates="equipment")


class Event(Base):
    __tablename__ = "events"

    event_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    equipment_id: Mapped[str] = mapped_column(
        ForeignKey("equipment.equipment_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    period: Mapped[str] = mapped_column(String(16), nullable=False)

    equipment: Mapped[Equipment] = relationship(back_populates="events")
    maintenance_records: Mapped[list[Maintenance]] = relationship(back_populates="event")


class Maintenance(Base):
    __tablename__ = "maintenance_history"

    maintenance_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    event_id: Mapped[str] = mapped_column(
        ForeignKey("events.event_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    equipment_id: Mapped[str] = mapped_column(
        ForeignKey("equipment.equipment_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    intervention_type: Mapped[str] = mapped_column(String(32), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    downtime_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    labor_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    parts_cost_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    parts_replaced_count: Mapped[int] = mapped_column(Integer, nullable=False)
    work_order_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    period: Mapped[str] = mapped_column(String(16), nullable=False)

    equipment: Mapped[Equipment] = relationship(back_populates="maintenance_records")
    event: Mapped[Event] = relationship(back_populates="maintenance_records")


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    __table_args__ = (
        UniqueConstraint(
            "equipment_id",
            "timestamp",
            "sensor_name",
            name="uq_sensor_logical_key",
        ),
        Index(
            "ix_sensor_eq_name_ts",
            "equipment_id",
            "sensor_name",
            "timestamp",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    equipment_id: Mapped[str] = mapped_column(
        ForeignKey("equipment.equipment_id", ondelete="RESTRICT"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timestamp_raw: Mapped[str] = mapped_column(String(40), nullable=False)
    sensor_name: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False)
    period: Mapped[str] = mapped_column(String(16), nullable=False)

    equipment: Mapped[Equipment] = relationship(back_populates="sensor_readings")
