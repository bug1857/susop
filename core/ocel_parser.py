import os
import pandas as pd
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import Dataset, Workspace
from app.core.ingestion import detect_delimiter

def parse_dataset_to_dataframe(
    dataset_id: UUID,
    tenant_id: UUID,
    workspace_id: UUID,
    db: Session
) -> pd.DataFrame:
    # 1. Fetch dataset metadata
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.workspace_id == workspace_id,
        Dataset.is_deleted == False
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found or has been deleted")
        
    if dataset.is_archived:
        raise HTTPException(status_code=400, detail="Cannot run process analysis on an archived dataset")
        
    # Check tenant access (Workspace -> Organization)
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace or workspace.organization_id != tenant_id:
        raise HTTPException(status_code=403, detail="Tenant access violation")
        
    # Verify mappings exist
    if not dataset.mappings:
        raise HTTPException(status_code=400, detail="Dataset mapping configuration is missing")
        
    # Find mapping keys
    mappings = dataset.mappings
    case_col = None
    activity_col = None
    timestamp_col = None
    object_id_col = None
    object_type_col = None
    carbon_col = None
    supplier_col = None
    
    for csv_header, mapped_role in mappings.items():
        if mapped_role == "case_id":
            case_col = csv_header
        elif mapped_role == "activity":
            activity_col = csv_header
        elif mapped_role == "timestamp":
            timestamp_col = csv_header
        elif mapped_role in ("object_ids", "object_id"):
            object_id_col = csv_header
        elif mapped_role == "object_type":
            object_type_col = csv_header
        elif mapped_role == "carbon_emissions":
            carbon_col = csv_header
        elif mapped_role == "supplier_id":
            supplier_col = csv_header
            
    # Validation checks
    if not case_col or not activity_col or not timestamp_col:
        raise HTTPException(
            status_code=400, 
            detail="Required process mapping fields (case_id, activity, timestamp) are missing in configurations"
        )
        
    if not os.path.exists(dataset.original_file_path):
        raise HTTPException(status_code=404, detail="Original dataset file not found in storage")
        
    # Load DataFrame
    try:
        delimiter = detect_delimiter(dataset.original_file_path)
        df = pd.read_csv(dataset.original_file_path, sep=delimiter)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed loading CSV file: {str(e)}")
        
    if df.empty:
        raise HTTPException(status_code=400, detail="Ingested event log is empty")
        
    # Verify columns exist in dataframe
    for col, name in [(case_col, "Case ID"), (activity_col, "Activity"), (timestamp_col, "Timestamp")]:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Mapped column '{col}' ({name}) not found in dataset file headers")
            
    # Parse Timestamps
    try:
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Timestamp parsing failure: {str(e)}")
        
    if df[timestamp_col].isnull().any():
        raise HTTPException(status_code=400, detail="Missing or malformed values detected in Timestamp column")
        
    # Project to standardized format for PM4Py
    rename_dict = {
        case_col: "case:concept:name",
        activity_col: "concept:name",
        timestamp_col: "time:timestamp"
    }
    
    if object_id_col and object_id_col in df.columns:
        rename_dict[object_id_col] = "object_id"
    if object_type_col and object_type_col in df.columns:
        rename_dict[object_type_col] = "object_type"
    if carbon_col and carbon_col in df.columns:
        rename_dict[carbon_col] = "carbon_emissions"
    if supplier_col and supplier_col in df.columns:
        rename_dict[supplier_col] = "supplier_id"
        
    df_mapped = df.rename(columns=rename_dict)
    
    # Force type conversions
    df_mapped["case:concept:name"] = df_mapped["case:concept:name"].astype(str)
    df_mapped["concept:name"] = df_mapped["concept:name"].astype(str)
    
    return df_mapped
