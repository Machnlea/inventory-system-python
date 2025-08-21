"""add predefined names to equipment categories

Revision ID: 007_add_predefined_names
Revises: 006_fix_auto_id
Create Date: 2025-08-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_add_predefined_names'
down_revision = '006_fix_auto_id'
branch_labels = None
depends_on = None


def upgrade():
    # Add predefined_names column to equipment_categories table
    op.add_column('equipment_categories', sa.Column('predefined_names', sa.JSON(), nullable=True))


def downgrade():
    # Remove predefined_names column from equipment_categories table
    op.drop_column('equipment_categories', 'predefined_names')