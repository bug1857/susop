"""sprint6_add_insight_metadata

Revision ID: b9bf65c2a09b
Revises: 9d83949ac0d3
Create Date: 2026-06-16 22:03:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: sa.Unicode = 'b9bf65c2a09b'
down_revision: Union[str, Sequence[str], None] = '9d83949ac0d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('ai_insights', sa.Column('insight_metadata', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('ai_insights', 'insight_metadata')
