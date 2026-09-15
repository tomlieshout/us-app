"""add activity_cycles + activity_submissions.cycle for per-user Play Again

Revision ID: 65c183150546
Revises: 4d1607a933e0
Create Date: 2026-09-15 00:00:00.000000

Supports the toggle/cycle feature on Would You Rather, Know Each Other,
and Who Would: each (user, activity_type) tracks which "cycle" (pass
through the content bank) they're currently on, and every submission is
tagged with the cycle it was made in. Play Again advances the cycle
without touching old submissions, so "have I already answered this" can
be scoped to the current cycle only while full history stays intact.

Every existing submission defaults to cycle=1, which is exactly correct -
they were all made before this feature existed, i.e. during everyone's
first (and so far only) cycle.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '65c183150546'
down_revision = '4d1607a933e0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'activity_cycles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('activity_type', sa.String(length=32), nullable=False),
        sa.Column('cycle', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'activity_type', name='uq_activity_cycle_user_type'),
    )
    with op.batch_alter_table('activity_cycles', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_activity_cycles_user_id'), ['user_id'], unique=False)

    with op.batch_alter_table('activity_submissions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cycle', sa.Integer(), nullable=False, server_default='1'))


def downgrade():
    with op.batch_alter_table('activity_submissions', schema=None) as batch_op:
        batch_op.drop_column('cycle')

    with op.batch_alter_table('activity_cycles', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_activity_cycles_user_id'))

    op.drop_table('activity_cycles')
