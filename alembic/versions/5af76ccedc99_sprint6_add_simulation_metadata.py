"""sprint6_add_simulation_metadata

Revision ID: 5af76ccedc99
Revises: 72d6a0f07c00
Create Date: 2026-06-16 22:38:09.423263

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5af76ccedc99'
down_revision: Union[str, Sequence[str], None] = '72d6a0f07c00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('scenario_simulations', sa.Column('scenario_type', sa.String(), nullable=False, server_default='EMISSION_REDUCTION'))
    op.add_column('scenario_simulations', sa.Column('simulation_confidence_score', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('scenario_simulations', sa.Column('simulation_metadata', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('scenario_simulations', 'simulation_metadata')
    op.drop_column('scenario_simulations', 'simulation_confidence_score')
    op.drop_column('scenario_simulations', 'scenario_type')
