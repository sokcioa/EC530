from sqlalchemy import Column, Integer, Boolean
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add new columns to errands table
    op.add_column('errands', Column('flexible_start_window', Boolean, default=False))
    op.add_column('errands', Column('flexible_end_window', Boolean, default=False))
    op.add_column('errands', Column('flexible_duration', Boolean, default=False))
    op.add_column('errands', Column('min_duration', Integer))
    op.add_column('errands', Column('max_duration', Integer))

def downgrade():
    # Remove the columns if we need to roll back
    op.drop_column('errands', 'flexible_start_window')
    op.drop_column('errands', 'flexible_end_window')
    op.drop_column('errands', 'flexible_duration')
    op.drop_column('errands', 'min_duration')
    op.drop_column('errands', 'max_duration') 