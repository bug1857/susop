"""sprint6_add_recommendation_metadata

Revision ID: 002d697a02e6
Revises: 5af76ccedc99
Create Date: 2026-06-16 23:04:09.491048

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002d697a02e6'
down_revision: Union[str, Sequence[str], None] = '5af76ccedc99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('ai_recommendations', sa.Column('recommendation_confidence_score', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('ai_recommendations', sa.Column('recommendation_metadata', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('ai_recommendations', 'recommendation_metadata')
    op.drop_column('ai_recommendations', 'recommendation_confidence_score')
