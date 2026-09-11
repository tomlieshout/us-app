"""add title_key for plans matching

Revision ID: 4d1607a933e0
Revises: 4dcccad2d49f
Create Date: 2026-09-11 22:43:16.813738

"""
import re

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '4d1607a933e0'
down_revision = '4dcccad2d49f'
branch_labels = None
depends_on = None


def _normalize_title(title):
    # Mirrors Plan.normalize_title exactly (app/models/plan.py) - trim,
    # collapse internal whitespace, casefold. Any existing rows (created
    # before this migration) get backfilled with the same normalization the
    # app now maintains automatically going forward.
    return re.sub(r"\s+", " ", (title or "").strip()).casefold()


def upgrade():
    # Added nullable first - added_column NOT NULL would fail outright
    # against any existing rows (no default value makes sense here, since
    # title_key is always derived from title). Backfilled below, then
    # tightened to NOT NULL once every row genuinely has a value.
    with op.batch_alter_table('plans', schema=None) as batch_op:
        batch_op.add_column(sa.Column('title_key', sa.String(length=200), nullable=True))

    plans = sa.table('plans', sa.column('id', sa.Integer), sa.column('title', sa.String), sa.column('title_key', sa.String))
    connection = op.get_bind()
    for plan_id, title in connection.execute(sa.select(plans.c.id, plans.c.title)):
        connection.execute(plans.update().where(plans.c.id == plan_id).values(title_key=_normalize_title(title)))

    with op.batch_alter_table('plans', schema=None) as batch_op:
        batch_op.alter_column('title_key', existing_type=sa.String(length=200), nullable=False)
        batch_op.create_index(batch_op.f('ix_plans_title_key'), ['title_key'], unique=False)


def downgrade():
    with op.batch_alter_table('plans', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_plans_title_key'))
        batch_op.drop_column('title_key')
