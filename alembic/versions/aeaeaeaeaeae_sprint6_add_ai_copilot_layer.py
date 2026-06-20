"""sprint6_add_ai_copilot_layer

Revision ID: aeaeaeaeaeae
Revises: c652d78c659a
Create Date: 2026-06-16 23:35:45.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aeaeaeaeaeae'
down_revision: Union[str, Sequence[str], None] = 'c652d78c659a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'ai_copilot_responses',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('analysis_id', sa.UUID(), nullable=True),
        sa.Column('entity_id', sa.UUID(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('request_type', sa.String(), nullable=False),
        sa.Column('prompt_version', sa.Integer(), nullable=False),
        sa.Column('prompt_hash', sa.String(), nullable=False),
        sa.Column('response_text', sa.String(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False),
        sa.Column('response_metadata', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['analysis_id'], ['process_analyses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_copilot_tenant', 'ai_copilot_responses', ['tenant_id'])
    op.create_index('idx_copilot_workspace', 'ai_copilot_responses', ['workspace_id'])
    op.create_index('idx_copilot_project', 'ai_copilot_responses', ['project_id'])
    op.create_index('idx_copilot_analysis', 'ai_copilot_responses', ['analysis_id'])
    op.create_index('idx_copilot_entity_id', 'ai_copilot_responses', ['entity_id'])
    op.create_index('idx_copilot_request_type', 'ai_copilot_responses', ['request_type'])
    op.create_index('idx_copilot_created_at', 'ai_copilot_responses', ['created_at'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('ai_copilot_responses')
