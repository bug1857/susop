"""sprint6_add_explainability_engine

Revision ID: c652d78c659a
Revises: 002d697a02e6
Create Date: 2026-06-16 23:13:34.658114

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c652d78c659a'
down_revision: Union[str, Sequence[str], None] = '002d697a02e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'ai_explainability',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('analysis_id', sa.UUID(), nullable=True),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=False),
        sa.Column('explanation_payload', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['analysis_id'], ['process_analyses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_explainability_tenant', 'ai_explainability', ['tenant_id'])
    op.create_index('idx_explainability_workspace', 'ai_explainability', ['workspace_id'])
    op.create_index('idx_explainability_project', 'ai_explainability', ['project_id'])
    op.create_index('idx_explainability_analysis', 'ai_explainability', ['analysis_id'])
    op.create_index('idx_explainability_entity_type', 'ai_explainability', ['entity_type'])
    op.create_index('idx_explainability_entity_id', 'ai_explainability', ['entity_id'])
    op.create_index('idx_explainability_created_at', 'ai_explainability', ['created_at'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('ai_explainability')
