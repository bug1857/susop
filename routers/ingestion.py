import os
import shutil
import uuid
import csv
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.core.audit import log_activity
from app.core.ingestion import detect_delimiter, validate_csv, detect_schema
from app.models.models import User, Dataset, Workspace
from app.schemas.schemas import DatasetResponse, SaveMappingRequest

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

UPLOAD_DIR = "storage"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def check_dataset_access(dataset_id: UUID, user_id: UUID, db: Session, required_roles: List[str]) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.is_deleted == False).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    # Verify user has access to the workspace owning this dataset
    RoleChecker(required_roles).check_workspace_role(dataset.workspace_id, user_id, db)
    return dataset

@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_csv(
    workspace_id: UUID = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Enforce backend role check on workspace
    RoleChecker(["Admin", "Manager", "Analyst"]).check_workspace_role(workspace_id, current_user.id, db)
    
    # Validate file format
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV file format is supported in Sprint 2")

    # Save file to storage
    file_id = uuid.uuid4()
    original_filename = file.filename
    original_path = os.path.join(UPLOAD_DIR, f"{file_id}_orig.csv")
    
    file_size = 0
    try:
        with open(original_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_size = os.path.getsize(original_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Check file size limit (50MB)
    if file_size > 50 * 1024 * 1024:
        if os.path.exists(original_path):
            os.remove(original_path)
        raise HTTPException(status_code=400, detail="File size exceeds the 50MB limit")

    # Read CSV metadata & check validation
    delimiter = detect_delimiter(original_path)
    headers, val_errors, row_count = validate_csv(original_path, delimiter)
    suggestions = detect_schema(headers)

    has_errors = any(err["row"] == 0 for err in val_errors)
    status_str = "validation_failed" if has_errors else "mapping_required"

    # Create dataset record
    new_dataset = Dataset(
        workspace_id=workspace_id,
        name=original_filename,
        original_file_path=original_path,
        file_size=file_size,
        status=status_str,
        dataset_type="csv",
        version=1,
        row_count=row_count,
        headers=headers,
        schema_confidence=suggestions,
        validation_errors=val_errors,
        uploaded_by=current_user.id,
        uploaded_at=datetime.utcnow()
    )
    db.add(new_dataset)
    db.commit()
    db.refresh(new_dataset)

    # Log audit logs
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    log_activity(db, user_id=current_user.id, action="dataset_version_created", tenant_id=workspace.organization_id, details=f"Dataset: {original_filename} (v1)")
    log_activity(db, user_id=current_user.id, action="validation_completed", tenant_id=workspace.organization_id, details=f"Validated: {original_filename} (status: {status_str})")

    return new_dataset

@router.get("/datasets", response_model=list[DatasetResponse])
def list_datasets(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Enforce tenant / workspace check
    RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_workspace_role(workspace_id, current_user.id, db)
    
    datasets = db.query(Dataset).filter(
        Dataset.workspace_id == workspace_id,
        Dataset.is_deleted == False
    ).order_by(Dataset.created_at.desc()).all()
    
    return datasets

@router.get("/datasets/{id}", response_model=DatasetResponse)
def get_dataset(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return check_dataset_access(id, current_user.id, db, ["Admin", "Manager", "Analyst", "Viewer"])

@router.put("/datasets/{id}/map", response_model=DatasetResponse)
def save_column_mapping(
    id: UUID,
    payload: SaveMappingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dataset = check_dataset_access(id, current_user.id, db, ["Admin", "Manager", "Analyst"])
    
    # Basic validation: ensure mappings are present
    if not payload.mappings:
        raise HTTPException(status_code=400, detail="Mapping configuration cannot be empty")
        
    dataset.mappings = payload.mappings
    dataset.status = "ready"
    dataset.mapping_saved_by = current_user.id
    dataset.mapping_saved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(dataset)
    
    workspace = db.query(Workspace).filter(Workspace.id == dataset.workspace_id).first()
    log_activity(db, user_id=current_user.id, action="mapping_updated", tenant_id=workspace.organization_id, details=f"Mappings saved for dataset: {dataset.name}")
    
    return dataset

@router.get("/datasets/{id}/preview")
def get_preview(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dataset = check_dataset_access(id, current_user.id, db, ["Admin", "Manager", "Analyst", "Viewer"])
    
    if not os.path.exists(dataset.original_file_path):
        raise HTTPException(status_code=404, detail="Original dataset file not found in local storage")
        
    preview_rows = []
    delimiter = detect_delimiter(dataset.original_file_path)
    
    try:
        with open(dataset.original_file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=delimiter)
            # Skip headers
            next(reader, None)
            for _ in range(10):
                row = next(reader, None)
                if row is None:
                    break
                preview_rows.append(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed loading preview: {str(e)}")
        
    return {
        "headers": dataset.headers,
        "preview": preview_rows,
        "mappings": dataset.mappings,
        "validation_errors": dataset.validation_errors
    }

@router.post("/datasets/{id}/archive", response_model=DatasetResponse)
def archive_dataset(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dataset = check_dataset_access(id, current_user.id, db, ["Admin", "Manager", "Analyst"])
    dataset.is_archived = True
    db.commit()
    db.refresh(dataset)
    
    workspace = db.query(Workspace).filter(Workspace.id == dataset.workspace_id).first()
    log_activity(db, user_id=current_user.id, action="dataset_archived", tenant_id=workspace.organization_id, details=f"Archived dataset: {dataset.name}")
    return dataset

@router.post("/datasets/{id}/restore", response_model=DatasetResponse)
def restore_dataset(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dataset = check_dataset_access(id, current_user.id, db, ["Admin", "Manager", "Analyst"])
    dataset.is_archived = False
    db.commit()
    db.refresh(dataset)
    
    workspace = db.query(Workspace).filter(Workspace.id == dataset.workspace_id).first()
    log_activity(db, user_id=current_user.id, action="dataset_restored", tenant_id=workspace.organization_id, details=f"Restored dataset: {dataset.name}")
    return dataset

@router.delete("/datasets/{id}", response_model=DatasetResponse)
def soft_delete_dataset(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dataset = check_dataset_access(id, current_user.id, db, ["Admin", "Manager"])
    dataset.is_deleted = True
    db.commit()
    db.refresh(dataset)
    
    workspace = db.query(Workspace).filter(Workspace.id == dataset.workspace_id).first()
    log_activity(db, user_id=current_user.id, action="dataset_deleted", tenant_id=workspace.organization_id, details=f"Soft deleted dataset: {dataset.name}")
    return dataset

@router.get("/datasets/{id}/sustainability-metrics")
def get_sustainability_metrics(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dataset = check_dataset_access(id, current_user.id, db, ["Admin", "Manager", "Analyst", "Viewer"])
    
    if not os.path.exists(dataset.original_file_path):
        raise HTTPException(status_code=404, detail="Original dataset file not found in storage")
        
    try:
        import pandas as pd
        delimiter = detect_delimiter(dataset.original_file_path)
        df = pd.read_csv(dataset.original_file_path, sep=delimiter)
        
        mappings = dataset.mappings or {}
        role_to_header = {}
        for header, role in mappings.items():
            role_to_header[role] = header
            
        supplier_id_col = role_to_header.get("supplier_id")
        supplier_name_col = role_to_header.get("supplier_name")
        carbon_col = role_to_header.get("carbon_emissions")
        cost_col = role_to_header.get("cost")
        risk_col = role_to_header.get("risk_level")
        country_col = role_to_header.get("supplier_country")
        category_col = role_to_header.get("purchase_category")
        
        suppliers = []
        if supplier_id_col and supplier_id_col in df.columns:
            name_col = supplier_name_col if (supplier_name_col and supplier_name_col in df.columns) else supplier_id_col
            cost_c = cost_col if (cost_col and cost_col in df.columns) else None
            carb_c = carbon_col if (carbon_col and carbon_col in df.columns) else None
            risk_c = risk_col if (risk_col and risk_col in df.columns) else None
            country_c = country_col if (country_col and country_col in df.columns) else None
            category_c = category_col if (category_col and category_col in df.columns) else None
            
            grouped = df.groupby(supplier_id_col)
            for supp_id, group in grouped:
                supp_name = str(group[name_col].iloc[0]) if not group[name_col].empty else str(supp_id)
                supp_country = str(group[country_c].iloc[0]) if (country_c and not group[country_c].empty) else "Unknown"
                
                if carb_c:
                    supp_emissions = float(pd.to_numeric(group[carb_c], errors="coerce").sum())
                else:
                    supp_emissions = 0.0
                    
                if cost_c:
                    supp_spend = float(pd.to_numeric(group[cost_c], errors="coerce").sum())
                else:
                    supp_spend = 0.0
                    
                if risk_c:
                    risk_counts = group[risk_c].value_counts()
                    supp_risk = str(risk_counts.index[0]) if not risk_counts.empty else "Low"
                else:
                    supp_risk = "Low"
                    
                supp_category = str(group[category_c].iloc[0]) if (category_c and not group[category_c].empty) else "Procurement"
                
                esg_score = 80
                if supp_risk == "High":
                    esg_score -= 20
                elif supp_risk == "Medium":
                    esg_score -= 10
                if supp_emissions > 50000:
                    esg_score -= 20
                elif supp_emissions > 10000:
                    esg_score -= 10
                esg_score = max(10, min(95, esg_score))
                
                suppliers.append({
                    "supplier_id": str(supp_id),
                    "supplier_name": supp_name,
                    "supplier_country": supp_country,
                    "emissions": supp_emissions,
                    "spend": supp_spend,
                    "risk_level": supp_risk,
                    "purchase_category": supp_category,
                    "esg_score": esg_score / 100.0
                })
                
        top_emissions = sorted(suppliers, key=lambda x: x["emissions"], reverse=True)
        top_spend = sorted(suppliers, key=lambda x: x["spend"], reverse=True)
        
        risk_map = {"High": 3, "Medium": 2, "Low": 1}
        risk_rankings = sorted(suppliers, key=lambda x: (risk_map.get(x["risk_level"], 1), x["spend"]), reverse=True)
        esg_rankings = sorted(suppliers, key=lambda x: x["esg_score"], reverse=True)
        
        energy_col = role_to_header.get("energy_kwh")
        water_col = role_to_header.get("water_liters")
        waste_col = role_to_header.get("waste_kg")
        
        total_energy = float(pd.to_numeric(df[energy_col], errors="coerce").sum()) if (energy_col and energy_col in df.columns) else 0.0
        total_water = float(pd.to_numeric(df[water_col], errors="coerce").sum()) if (water_col and water_col in df.columns) else 0.0
        total_waste = float(pd.to_numeric(df[waste_col], errors="coerce").sum()) if (waste_col and waste_col in df.columns) else 0.0
        
        timestamp_col = role_to_header.get("timestamp")
        monthly_emissions = []
        if timestamp_col and timestamp_col in df.columns and carbon_col and carbon_col in df.columns:
            df_copy = df.copy()
            df_copy["parsed_time"] = pd.to_datetime(df_copy[timestamp_col], errors="coerce")
            df_copy["month_str"] = df_copy["parsed_time"].dt.strftime("%Y-%m")
            df_copy["carbon_val"] = pd.to_numeric(df_copy[carbon_col], errors="coerce")
            trend_grouped = df_copy.groupby("month_str")["carbon_val"].sum().sort_index()
            for month, val in trend_grouped.items():
                if pd.notnull(month):
                    monthly_emissions.append({
                        "month": str(month),
                        "emissions": float(val)
                    })
                    
        return {
            "success": True,
            "data": {
                "suppliers": suppliers,
                "top_suppliers_emissions": top_emissions[:5],
                "top_suppliers_spend": top_spend[:5],
                "supplier_risk_rankings": risk_rankings[:5],
                "supplier_esg_rankings": esg_rankings[:5],
                "total_energy_kwh": total_energy,
                "total_water_liters": total_water,
                "total_waste_kg": total_waste,
                "monthly_emissions": monthly_emissions
            },
            "errors": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed calculating sustainability metrics: {str(e)}")
