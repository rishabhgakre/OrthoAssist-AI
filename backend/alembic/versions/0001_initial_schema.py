"""initial schema — doctors, patients, xray_records, gait_records, cori_records

Hand-written to exactly match app/models/models.py as of the first
production deployment. Every migration after this one should be generated
with `alembic revision --autogenerate -m "..."` following a models.py
change, then reviewed before committing (autogenerate is a strong first
draft, not a guarantee — it doesn't reliably detect column renames, for
example, and will generate a drop+add instead unless you edit it).

Revision ID: 0001
Revises:
Create Date: 2026-09-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "doctors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_doctors_id", "doctors", ["id"])
    op.create_index("ix_doctors_email", "doctors", ["email"], unique=True)

    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("doctors.id"), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("gender", sa.String(), nullable=True),
        sa.Column("bone_type", sa.String(), nullable=True),
        sa.Column("injury_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_patients_id", "patients", ["id"])

    op.create_table(
        "xray_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=True),
        sa.Column("pre_image_path", sa.String(), nullable=False),
        sa.Column("post_image_path", sa.String(), nullable=False),
        sa.Column("pre_annotated_path", sa.String(), nullable=True),
        sa.Column("post_annotated_path", sa.String(), nullable=True),
        sa.Column("pre_detection_confidence", sa.Float(), nullable=True),
        sa.Column("post_detection_confidence", sa.Float(), nullable=True),
        sa.Column("pre_gap_mm", sa.Float(), nullable=True),
        sa.Column("pre_alignment_pct", sa.Float(), nullable=True),
        sa.Column("pre_continuity_pct", sa.Float(), nullable=True),
        sa.Column("pre_bone_angle_deg", sa.Float(), nullable=True),
        sa.Column("post_gap_mm", sa.Float(), nullable=True),
        sa.Column("post_alignment_pct", sa.Float(), nullable=True),
        sa.Column("post_continuity_pct", sa.Float(), nullable=True),
        sa.Column("post_bone_angle_deg", sa.Float(), nullable=True),
        sa.Column("gap_improvement_pct", sa.Float(), nullable=True),
        sa.Column("alignment_improvement_pct", sa.Float(), nullable=True),
        sa.Column("continuity_improvement_pct", sa.Float(), nullable=True),
        sa.Column("structural_recovery_score", sa.Float(), nullable=True),
        sa.Column("raw_measurements", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_xray_records_id", "xray_records", ["id"])

    op.create_table(
        "gait_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=True),
        sa.Column("video_path", sa.String(), nullable=False),
        sa.Column("annotated_video_path", sa.String(), nullable=True),
        sa.Column("walking_speed", sa.Float(), nullable=True),
        sa.Column("cadence", sa.Float(), nullable=True),
        sa.Column("stride_length", sa.Float(), nullable=True),
        sa.Column("step_length", sa.Float(), nullable=True),
        sa.Column("step_symmetry", sa.Float(), nullable=True),
        sa.Column("knee_flexion", sa.Float(), nullable=True),
        sa.Column("hip_movement", sa.Float(), nullable=True),
        sa.Column("balance_score", sa.Float(), nullable=True),
        sa.Column("functional_recovery_score", sa.Float(), nullable=True),
        sa.Column("raw_measurements", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_gait_records_id", "gait_records", ["id"])

    op.create_table(
        "cori_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=True),
        sa.Column("xray_record_id", sa.Integer(), sa.ForeignKey("xray_records.id"), nullable=True),
        sa.Column("gait_record_id", sa.Integer(), sa.ForeignKey("gait_records.id"), nullable=True),
        sa.Column("structural_score", sa.Float(), nullable=True),
        sa.Column("functional_score", sa.Float(), nullable=True),
        sa.Column("weight_structural", sa.Float(), nullable=True),
        sa.Column("weight_functional", sa.Float(), nullable=True),
        sa.Column("cori_score", sa.Float(), nullable=True),
        sa.Column("report_pdf_path", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_cori_records_id", "cori_records", ["id"])


def downgrade() -> None:
    # Reverse FK dependency order: children before parents.
    op.drop_index("ix_cori_records_id", table_name="cori_records")
    op.drop_table("cori_records")

    op.drop_index("ix_gait_records_id", table_name="gait_records")
    op.drop_table("gait_records")

    op.drop_index("ix_xray_records_id", table_name="xray_records")
    op.drop_table("xray_records")

    op.drop_index("ix_patients_id", table_name="patients")
    op.drop_table("patients")

    op.drop_index("ix_doctors_email", table_name="doctors")
    op.drop_index("ix_doctors_id", table_name="doctors")
    op.drop_table("doctors")
