"""adding event stat id

Revision ID: 9bd534a4f694
Revises: 46e9e4b0831c
Create Date: 2023-03-14 08:38:46.291672

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9bd534a4f694"
down_revision = "46e9e4b0831c"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("event", sa.Column("stat_id", sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("event", "stat_id")
    # ### end Alembic commands ###
