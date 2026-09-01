"""Ajout table sensor_readings avec clé logique unique.

Revision ID: 002_sensor_readings
Revises: 001_initial_m2
Create Date: 2026-08-24

downgrade : supprime la table sensor_readings et son index ; les tables M2 restent.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_sensor_readings"
down_revision: Union[str, None] = "001_initial_m2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sensor_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("equipment_id", sa.String(length=32), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timestamp_raw", sa.String(length=40), nullable=False),
        sa.Column("sensor_name", sa.String(length=32), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=16), nullable=False),
        sa.Column("period", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.equipment_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "equipment_id",
            "timestamp",
            "sensor_name",
            name="uq_sensor_logical_key",
        ),
    )
    with op.batch_alter_table("sensor_readings", schema=None) as batch_op:
        batch_op.create_index(
            "ix_sensor_eq_name_ts",
            ["equipment_id", "sensor_name", "timestamp"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_table("sensor_readings")
