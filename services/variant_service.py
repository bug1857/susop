import pandas as pd
from uuid import UUID
from sqlalchemy.orm import Session
from typing import List
from app.repositories.process_variant_repository import ProcessVariantRepository
from app.models.models import ProcessVariant

class VariantService:
    def __init__(self, db: Session):
        self.db = db
        self.variant_repo = ProcessVariantRepository(db)

    def generate_and_save_variants(
        self, 
        df: pd.DataFrame, 
        analysis_id: UUID, 
        tenant_id: UUID, 
        workspace_id: UUID, 
        project_id: UUID
    ) -> List[ProcessVariant]:
        # Sort values to ensure chronological sequence per case
        df_sorted = df.sort_values(by=["case:concept:name", "time:timestamp"])
        
        # Group by case and construct the list of activities
        case_groups = df_sorted.groupby("case:concept:name")["concept:name"].apply(list)
        total_cases = len(case_groups)
        
        if total_cases == 0:
            return []
            
        # Group sequences together to count frequencies
        sequence_counts = case_groups.apply(tuple).value_counts()
        
        variants = []
        for idx, (sequence, freq) in enumerate(sequence_counts.items(), start=1):
            pct = float(freq) / total_cases
            variant_name = f"Variant {idx}"
            
            pv = ProcessVariant(
                analysis_id=analysis_id,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                project_id=project_id,
                variant_name=variant_name,
                frequency=int(freq),
                percentage=pct,
                activity_sequence=list(sequence),
                is_deleted=False
            )
            variants.append(self.variant_repo.create(pv))
            
        return variants

    def get_variants(self, analysis_id: UUID, tenant_id: UUID) -> List[ProcessVariant]:
        return self.variant_repo.get_by_analysis(analysis_id, tenant_id)
