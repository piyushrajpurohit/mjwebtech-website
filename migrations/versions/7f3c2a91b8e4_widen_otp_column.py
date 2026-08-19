"""Widen OTP column for hashed codes.

Revision ID: 7f3c2a91b8e4
Revises: 42475c39c0b9
Create Date: 2026-08-19
"""
from alembic import op
import sqlalchemy as sa


revision = "7f3c2a91b8e4"
down_revision = "42475c39c0b9"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("otp_verifications", schema=None) as batch_op:
        batch_op.alter_column(
            "otp",
            existing_type=sa.String(length=6),
            type_=sa.String(length=255),
            existing_nullable=False,
        )


def downgrade():
    with op.batch_alter_table("otp_verifications", schema=None) as batch_op:
        batch_op.alter_column(
            "otp",
            existing_type=sa.String(length=255),
            type_=sa.String(length=6),
            existing_nullable=False,
        )
