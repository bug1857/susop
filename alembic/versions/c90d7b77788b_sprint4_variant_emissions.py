"""sprint4_variant_emissions

Revision ID: c90d7b77788b
Revises: 1479763bed69
Create Date: 2026-06-16 18:04:48.220873

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c90d7b77788b'
down_revision: Union[str, Sequence[str], None] = '1479763bed69'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('process_variants', sa.Column('total_emissions', sa.Float(), nullable=True))
    op.add_column('process_variants', sa.Column('average_emissions', sa.Float(), nullable=True))
    op.add_column('process_variants', sa.Column('emissions_per_execution', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('process_variants', 'emissions_per_execution')
    op.drop_column('process_variants', 'average_emissions')
    op.drop_column('process_variants', 'total_emissions')
