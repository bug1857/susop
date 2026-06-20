# Sprint 2 Completion Report — Data Ingestion Engine

This report summarizes the design, implementation, and verification outcomes for the **Data Ingestion Engine** (Sprint 2) of SustainOCPM.

---

## 1. Feature Phase Classification (MVP Protection)

All ingestion features have been validated against our MVP constraints to safeguard development velocity and maintain clear boundaries.

| Feature Area | Phase | Business Value / Purpose | Scope Boundaries Met |
| :--- | :--- | :--- | :--- |
| **CSV File Upload** | **MVP** | Allows users to upload legacy and raw tabular logs (< 50MB) | Restrict inputs to `.csv` format only; storage local sandbox. |
| **Structural CSV Validation** | **MVP** | Guarantees file integrity before schema matching | Checks delimiter sniffing, blank rows, inconsistent columns, duplicate headers. |
| **Schema Mapping Wizard** | **MVP** | Auto-detects core process roles and enables manual override | Mapped roles: `case_id`, `activity`, `timestamp`, `carbon_emissions`, `supplier_id`. |
| **Data Preview Table** | **MVP** | Renders first 10 parsed rows based on mapping configurations | Visual validation of parsed rows before committing database transaction. |
| **Data Lineage Tracking** | **V1** | Retains creator IDs, edit records, versions, and original files | Implemented as persistent auditing metadata inside the `datasets` schema. |
| **Soft Delete & Archiving** | **V1** | Prevent data loss, maintaining end-to-end traceability | Soft deletes set `is_deleted = True`; archiving supports restore switches. |

---

## 2. Ingestion Operations Verification

### Delimiter & Parser Sniffing
* Sniffs delimiters (`,`, `;`, `\t`, `|`) and handles UTF-8-sig BOM headers seamlessly.
* Blocks malformed files (empty headers, size violations, invalid UTF-8 encoding).

### Auto-Detection Confidence Match Rates
* **Event ID:** `event_id`, `uuid` (95% confidence)
* **Case ID:** `case_id`, `order_no` (90% confidence)
* **Activity:** `activity`, `concept:name` (95% confidence)
* **Timestamp:** `timestamp`, `created_at` (95% confidence)
* **Carbon Emissions:** `co2`, `emissions` (90% confidence)
* **Supplier ID:** `supplier_id`, `vendor` (90% confidence)

---

## 3. Core Verification Outcomes

### Automated Integration Tests
We successfully ran all pytest suites covering upload, parsing, mapping validations, archiving, and workspace isolation checks:
```bash
$ PYTHONPATH=. venv/bin/pytest
======================== 3 passed, 36 warnings in 2.39s ========================
```
* **Test cases verified:**
  1. `test_signup_and_login` - Validates session tokens and password hashing.
  2. `test_organizations_and_workspaces` - Confirms organization boundaries and workspace parameters.
  3. `test_csv_upload_validation_and_preview` - Checks CSV parser, schema auto-suggestions, mapping overrides, soft deletes, and archive/restore states.

### Multi-Tenant Isolation
* Workspace-level RBAC is enforced on the ingestion API layer. All requests validate token identity scopes (`workspace_role` checks) before returning dataset details, preventing cross-tenant data leaking.

---

## 4. Future Foundations Created

The Sprint 2 implementation incorporates essential extension hooks designed to enable downstream analytics:

1. **Object-Centric Process Mining (OCPM) / OCEL 2.0 Ingestion**: The database model defines `parent_dataset_id` and `dataset_type` (supporting placeholders like `ocel` and `json`), simplifying the process of connecting event-object relationship logs in future sprints.
2. **Carbon Fitness & Attribution**: Built-in mapping selector hooks capture `carbon_emissions` and `supplier_id` columns, storing them as metadata parameters. These coordinates will directly feed the carbon conformance engines and supplier ESG attribution scoring mechanisms in Sprint 3.
3. **Traceability & Lineage Audit Logs**: Fields like `uploaded_by`, `uploaded_at`, `mapping_saved_by`, and `mapping_saved_at` establish a complete data lineage history. This foundation will drive compliance generation and audit logs (BRSR Reporting) during business process audits.
