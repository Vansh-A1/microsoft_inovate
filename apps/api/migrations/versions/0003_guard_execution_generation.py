"""Prevent an older same-version evaluation intent from publishing over a newer request."""
from alembic import op
import sqlalchemy as sa
revision='0003_generation'
down_revision='0002_inputs'
branch_labels=None
depends_on=None


def upgrade():
    op.add_column('jobs',sa.Column('generation',sa.Integer(),nullable=False,server_default='0'))
    op.alter_column('jobs','generation',server_default=None)


def downgrade():
    op.drop_column('jobs','generation')
