"""sprint4_conformance_patch

Revision ID: 1479763bed69
Revises: 2a4c95ff1c79
Create Date: 2026-06-16 18:00:16.039330

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1479763bed69'
down_revision: Union[str, Sequence[str], None] = '2a4c95ff1c79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('conformance_deviations', sa.Column('trace_reference', sa.String(), nullable=True))
    op.add_column('conformance_deviations', sa.Column('evidence_payload', sa.JSON(), nullable=True))
    op.add_column('conformance_results', sa.Column('conformance_method', sa.String(), nullable=True))
    op.add_column('conformance_results', sa.Column('execution_time_ms', sa.Integer(), nullable=True))
    op.add_column('conformance_results', sa.Column('diagnostic_trace_count', sa.Integer(), nullable=True))
    op.add_column('conformance_results', sa.Column('non_conforming_trace_count', sa.Integer(), nullable=True))
    op.add_column('conformance_results', sa.Column('reference_model_version', sa.Integer(), nullable=True))
    op.add_column('conformance_results', sa.Column('reference_model_id', sa.UUID(), nullable=True))
    op.add_column('conformance_results', sa.Column('failure_reason', sa.String(), nullable=True))
    op.add_column('conformance_results', sa.Column('dataset_id', sa.UUID(), nullable=True))
    op.add_column('conformance_results', sa.Column('analysis_version', sa.Integer(), nullable=True))
    
    # SQLite friendly constraints can be added with names
    with op.batch_alter_table('conformance_results') as batch_op:
        batch_op.create_foreign_key('fk_conformance_results_dataset_id', 'datasets', ['dataset_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_conformance_results_reference_model_id', 'reference_models', ['reference_model_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('conformance_results') as batch_op:
        batch_op.drop_constraint('fk_conformance_results_reference_model_id', type_='foreignkey')
        batch_op.drop_constraint('fk_conformance_results_dataset_id', type_='foreignkey')
        
    op.drop_column('conformance_results', 'analysis_version')
    op.drop_column('conformance_results', 'dataset_id')
    op.drop_column('conformance_results', 'failure_reason')
    op.drop_column('conformance_results', 'reference_model_id')
    op.drop_column('conformance_results', 'reference_model_version')
    op.drop_column('conformance_results', 'non_conforming_trace_count')
    op.drop_column('conformance_results', 'diagnostic_trace_count')
    op.drop_column('conformance_results', 'execution_time_ms')
    op.drop_column('conformance_results', 'conformance_method')
    op.drop_column('conformance_deviations', 'evidence_payload')
    op.drop_column('conformance_deviations', 'trace_reference')
