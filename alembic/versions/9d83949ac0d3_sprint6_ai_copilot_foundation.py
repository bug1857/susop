"""sprint6_ai_copilot_foundation

Revision ID: 9d83949ac0d3
Revises: ff870c70b120
Create Date: 2026-06-16 21:45:40.550478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: sa.Unicode = '9d83949ac0d3'
down_revision: Union[str, Sequence[str], None] = 'ff870c70b120'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create Table: ai_insights
    op.create_table('ai_insights',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('workspace_id', sa.UUID(), nullable=False),
    sa.Column('project_id', sa.UUID(), nullable=False),
    sa.Column('analysis_id', sa.UUID(), nullable=True),
    sa.Column('insight_type', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('severity', sa.String(), nullable=False),
    sa.Column('confidence_score', sa.Float(), nullable=False),
    sa.Column('source_entity', sa.String(), nullable=True),
    sa.Column('source_reference', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['process_analyses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_insights_tenant_id'), 'ai_insights', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_ai_insights_workspace_id'), 'ai_insights', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_ai_insights_project_id'), 'ai_insights', ['project_id'], unique=False)
    op.create_index(op.f('ix_ai_insights_analysis_id'), 'ai_insights', ['analysis_id'], unique=False)
    op.create_index(op.f('ix_ai_insights_status'), 'ai_insights', ['status'], unique=False)
    op.create_index(op.f('ix_ai_insights_created_at'), 'ai_insights', ['created_at'], unique=False)
    op.create_index(op.f('ix_ai_insights_insight_type'), 'ai_insights', ['insight_type'], unique=False)

    # Create Table: carbon_forecasts
    op.create_table('carbon_forecasts',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('workspace_id', sa.UUID(), nullable=False),
    sa.Column('project_id', sa.UUID(), nullable=False),
    sa.Column('analysis_id', sa.UUID(), nullable=True),
    sa.Column('forecast_period', sa.String(), nullable=False),
    sa.Column('forecast_method', sa.String(), nullable=False),
    sa.Column('predicted_emissions', sa.Float(), nullable=False),
    sa.Column('lower_bound', sa.Float(), nullable=False),
    sa.Column('upper_bound', sa.Float(), nullable=False),
    sa.Column('forecast_metadata', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['process_analyses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_carbon_forecasts_tenant_id'), 'carbon_forecasts', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_carbon_forecasts_workspace_id'), 'carbon_forecasts', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_carbon_forecasts_project_id'), 'carbon_forecasts', ['project_id'], unique=False)
    op.create_index(op.f('ix_carbon_forecasts_analysis_id'), 'carbon_forecasts', ['analysis_id'], unique=False)
    op.create_index(op.f('ix_carbon_forecasts_created_at'), 'carbon_forecasts', ['created_at'], unique=False)

    # Create Table: scenario_simulations
    op.create_table('scenario_simulations',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('workspace_id', sa.UUID(), nullable=False),
    sa.Column('project_id', sa.UUID(), nullable=False),
    sa.Column('analysis_id', sa.UUID(), nullable=True),
    sa.Column('scenario_name', sa.String(), nullable=False),
    sa.Column('scenario_description', sa.String(), nullable=True),
    sa.Column('input_parameters', sa.JSON(), nullable=False),
    sa.Column('baseline_emissions', sa.Float(), nullable=False),
    sa.Column('simulated_emissions', sa.Float(), nullable=False),
    sa.Column('emission_reduction', sa.Float(), nullable=False),
    sa.Column('reduction_percentage', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['process_analyses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scenario_simulations_tenant_id'), 'scenario_simulations', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_scenario_simulations_workspace_id'), 'scenario_simulations', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_scenario_simulations_project_id'), 'scenario_simulations', ['project_id'], unique=False)
    op.create_index(op.f('ix_scenario_simulations_analysis_id'), 'scenario_simulations', ['analysis_id'], unique=False)
    op.create_index(op.f('ix_scenario_simulations_created_at'), 'scenario_simulations', ['created_at'], unique=False)

    # Create Table: ai_recommendations
    op.create_table('ai_recommendations',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('workspace_id', sa.UUID(), nullable=False),
    sa.Column('project_id', sa.UUID(), nullable=False),
    sa.Column('analysis_id', sa.UUID(), nullable=True),
    sa.Column('recommendation_type', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('estimated_emission_reduction', sa.Float(), nullable=False),
    sa.Column('estimated_cost_reduction', sa.Float(), nullable=True),
    sa.Column('priority', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['process_analyses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_recommendations_tenant_id'), 'ai_recommendations', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_ai_recommendations_workspace_id'), 'ai_recommendations', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_ai_recommendations_project_id'), 'ai_recommendations', ['project_id'], unique=False)
    op.create_index(op.f('ix_ai_recommendations_analysis_id'), 'ai_recommendations', ['analysis_id'], unique=False)
    op.create_index(op.f('ix_ai_recommendations_status'), 'ai_recommendations', ['status'], unique=False)
    op.create_index(op.f('ix_ai_recommendations_created_at'), 'ai_recommendations', ['created_at'], unique=False)
    op.create_index(op.f('ix_ai_recommendations_recommendation_type'), 'ai_recommendations', ['recommendation_type'], unique=False)

    # Create Table: recommendation_evidence
    op.create_table('recommendation_evidence',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('recommendation_id', sa.UUID(), nullable=False),
    sa.Column('entity_type', sa.String(), nullable=False),
    sa.Column('entity_id', sa.UUID(), nullable=False),
    sa.Column('evidence_payload', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['recommendation_id'], ['ai_recommendations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recommendation_evidence_recommendation_id'), 'recommendation_evidence', ['recommendation_id'], unique=False)
    op.create_index(op.f('ix_recommendation_evidence_entity_type'), 'recommendation_evidence', ['entity_type'], unique=False)
    op.create_index(op.f('ix_recommendation_evidence_entity_id'), 'recommendation_evidence', ['entity_id'], unique=False)
    op.create_index(op.f('ix_recommendation_evidence_created_at'), 'recommendation_evidence', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_recommendation_evidence_created_at'), table_name='recommendation_evidence')
    op.drop_index(op.f('ix_recommendation_evidence_entity_id'), table_name='recommendation_evidence')
    op.drop_index(op.f('ix_recommendation_evidence_entity_type'), table_name='recommendation_evidence')
    op.drop_index(op.f('ix_recommendation_evidence_recommendation_id'), table_name='recommendation_evidence')
    op.drop_table('recommendation_evidence')

    op.drop_index(op.f('ix_ai_recommendations_recommendation_type'), table_name='ai_recommendations')
    op.drop_index(op.f('ix_ai_recommendations_created_at'), table_name='ai_recommendations')
    op.drop_index(op.f('ix_ai_recommendations_status'), table_name='ai_recommendations')
    op.drop_index(op.f('ix_ai_recommendations_analysis_id'), table_name='ai_recommendations')
    op.drop_index(op.f('ix_ai_recommendations_project_id'), table_name='ai_recommendations')
    op.drop_index(op.f('ix_ai_recommendations_workspace_id'), table_name='ai_recommendations')
    op.drop_index(op.f('ix_ai_recommendations_tenant_id'), table_name='ai_recommendations')
    op.drop_table('ai_recommendations')

    op.drop_index(op.f('ix_scenario_simulations_created_at'), table_name='scenario_simulations')
    op.drop_index(op.f('ix_scenario_simulations_analysis_id'), table_name='scenario_simulations')
    op.drop_index(op.f('ix_scenario_simulations_project_id'), table_name='scenario_simulations')
    op.drop_index(op.f('ix_scenario_simulations_workspace_id'), table_name='scenario_simulations')
    op.drop_index(op.f('ix_scenario_simulations_tenant_id'), table_name='scenario_simulations')
    op.drop_table('scenario_simulations')

    op.drop_index(op.f('ix_carbon_forecasts_created_at'), table_name='carbon_forecasts')
    op.drop_index(op.f('ix_carbon_forecasts_analysis_id'), table_name='carbon_forecasts')
    op.drop_index(op.f('ix_carbon_forecasts_project_id'), table_name='carbon_forecasts')
    op.drop_index(op.f('ix_carbon_forecasts_workspace_id'), table_name='carbon_forecasts')
    op.drop_index(op.f('ix_carbon_forecasts_tenant_id'), table_name='carbon_forecasts')
    op.drop_table('carbon_forecasts')

    op.drop_index(op.f('ix_ai_insights_insight_type'), table_name='ai_insights')
    op.drop_index(op.f('ix_ai_insights_created_at'), table_name='ai_insights')
    op.drop_index(op.f('ix_ai_insights_status'), table_name='ai_insights')
    op.drop_index(op.f('ix_ai_insights_analysis_id'), table_name='ai_insights')
    op.drop_index(op.f('ix_ai_insights_project_id'), table_name='ai_insights')
    op.drop_index(op.f('ix_ai_insights_workspace_id'), table_name='ai_insights')
    op.drop_index(op.f('ix_ai_insights_tenant_id'), table_name='ai_insights')
    op.drop_table('ai_insights')
