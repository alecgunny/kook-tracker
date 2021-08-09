"""first migration

Revision ID: 46e9e4b0831c
Revises: 
Create Date: 2020-12-07 09:09:06.385484

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "46e9e4b0831c"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "athlete",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "season",
        sa.Column("year", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("year"),
    )
    op.create_table(
        "event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["year"],
            ["season.year"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "round",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=True),
        sa.Column("number", sa.Integer(), nullable=True),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["event.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "heat",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=True),
        sa.Column("status", sa.Integer(), nullable=True),
        sa.Column("round_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["round_id"],
            ["round.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "heat_result",
        sa.Column("heat_id", sa.Integer(), nullable=False),
        sa.Column("athlete_id", sa.Integer(), nullable=True),
        sa.Column("index", sa.Integer(), nullable=False),
        sa.Column("score", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.ForeignKeyConstraint(
            ["athlete_id"],
            ["athlete.id"],
        ),
        sa.ForeignKeyConstraint(
            ["heat_id"],
            ["heat.id"],
        ),
        sa.PrimaryKeyConstraint("heat_id", "index"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("heat_result")
    op.drop_table("heat")
    op.drop_table("round")
    op.drop_table("event")
    op.drop_table("season")
    op.drop_table("athlete")
    # ### end Alembic commands ###
