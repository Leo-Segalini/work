"""Schéma initial M2 : equipment, events, maintenance_history.

Revision ID: 001_initial_m2
Revises:
Create Date: 2026-08-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial_m2"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "equipment",
        sa.Column("equipment_id", sa.String(length=32), nullable=False),
        sa.Column("equipment_type", sa.String(length=64), nullable=False),
        sa.Column("site_id", sa.String(length=32), nullable=False),
        sa.Column("commissioning_date", sa.Date(), nullable=True),
        sa.Column("criticality", sa.String(length=16), nullable=False),
        sa.Column("manufacturer", sa.String(length=64), nullable=True),
        sa.Column("rated_power_kw", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("equipment_id"),
    )
    with op.batch_alter_table("equipment", schema=None) as batch_op:
        batch_op.create_index("ix_equipment_site_id", ["site_id"], unique=False)

    op.create_table(
        "events",
        sa.Column("event_id", sa.String(length=32), nullable=False),
        sa.Column("equipment_id", sa.String(length=32), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("period", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.equipment_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("event_id"),
    )
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.create_index("ix_events_equipment_id", ["equipment_id"], unique=False)

    op.create_table(
        "maintenance_history",
        sa.Column("maintenance_id", sa.String(length=32), nullable=False),
        sa.Column("event_id", sa.String(length=32), nullable=False),
        sa.Column("equipment_id", sa.String(length=32), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("intervention_type", sa.String(length=32), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("downtime_minutes", sa.Integer(), nullable=False),
        sa.Column("labor_hours", sa.Float(), nullable=True),
        sa.Column("parts_cost_eur", sa.Float(), nullable=True),
        sa.Column("parts_replaced_count", sa.Integer(), nullable=False),
        sa.Column("work_order_note", sa.Text(), nullable=False),
        sa.Column("period", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.equipment_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["event_id"], ["events.event_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("maintenance_id"),
    )
    with op.batch_alter_table("maintenance_history", schema=None) as batch_op:
        batch_op.create_index("ix_maintenance_history_equipment_id", ["equipment_id"], unique=False)
        batch_op.create_index("ix_maintenance_history_event_id", ["event_id"], unique=False)


def downgrade() -> None:
    op.drop_table("maintenance_history")
    op.drop_table("events")
    with op.batch_alter_table("equipment", schema=None) as batch_op:
        batch_op.drop_index("ix_equipment_site_id")
    op.drop_table("equipment")
