"""sprint6_add_forecast_confidence_score

Revision ID: 72d6a0f07c00
Revises: b9bf65c2a09b
Create Date: 2026-06-16 22:26:52.657019

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '72d6a0f07c00'
down_revision: Union[str, Sequence[str], None] = 'b9bf65c2a09b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('carbon_forecasts', sa.Column('forecast_confidence_score', sa.Float(), nullable=False, server_default='0.0'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('carbon_forecasts', 'forecast_confidence_score')
