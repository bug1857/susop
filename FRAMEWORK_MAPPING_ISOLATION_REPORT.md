# Framework Mapping Tenant Isolation Validation Report

This report documents the verification and validation of tenant isolation and anti-enumeration security controls for ESG Framework Mappings on the SustainOCPM platform.

---

## 1. Test Setup

To validate complete tenant isolation, we configured two distinct tenants with separate credentials, organizations, KPIs, and framework mappings:

*   **Global Framework**: BRSR (id: `594c8317-c30b-4ce2-8ce1-0f80107deb8d`)
*   **Tenant A (Admin)**: `tenant_a@company.com`
    *   **Organization A**: Tenant A Org (id: `org_a_id`)
    *   **KPIs Registered**:
        *   `KPI_A_1` (id: `36be655e-919f-4cb7-a4c8-2fd539ec927e`, category: Environmental)
        *   `KPI_A_2` (id: `2636c38e-e11c-4677-835b-4707f452affb`, category: Social)
    *   **Mappings Created**:
        *   `KPI_A_1` → BRSR Mapping (Section A, Question Q1)
        *   `KPI_A_2` → BRSR Mapping (Section B, Question Q2)
*   **Tenant B (Admin)**: `tenant_b@company.com`
    *   **Organization B**: Tenant B Org (id: `org_b_id`)
    *   **KPIs Registered**:
        *   `KPI_B_1` (id: `3cc46797-9e7c-477f-9d00-a0e8c8d93aef`, category: Environmental)
        *   `KPI_B_2` (id: `df2ecaee-4437-4aa2-be99-7eaf389a0c36`, category: Social)
    *   **Mappings Created**:
        *   `KPI_B_1` → BRSR Mapping (Section C, Question Q3)
        *   `KPI_B_2` → BRSR Mapping (Section D, Question Q4)

---

## 2. API Validation Test Cases

### Test 1: Authenticate as Tenant A
*   **Request**: `GET /api/v1/esg/frameworks/594c8317-c30b-4ce2-8ce1-0f80107deb8d/mappings?tenant_id=org_a_id`
*   **Headers**: `Authorization: Bearer <Tenant_A_Token>`
*   **API Response**:
    ```json
    {
      "success": true,
      "data": [
        {
          "id": "66fd41bb-9f5d-4bf3-b6e4-456ccac4c764",
          "framework_id": "594c8317-c30b-4ce2-8ce1-0f80107deb8d",
          "kpi_definition_id": "36be655e-919f-4cb7-a4c8-2fd539ec927e",
          "framework_section": "Sec A",
          "framework_principle": null,
          "framework_question": "Q1",
          "reporting_category": "Mandatory",
          "created_at": "2026-06-16T14:36:08.900057"
        },
        {
          "id": "d54fdf45-4928-409d-9216-d5dea547d72c",
          "framework_id": "594c8317-c30b-4ce2-8ce1-0f80107deb8d",
          "kpi_definition_id": "2636c38e-e11c-4677-835b-4707f452affb",
          "framework_section": "Sec B",
          "framework_principle": null,
          "framework_question": "Q2",
          "reporting_category": "Mandatory",
          "created_at": "2026-06-16T14:36:08.900060"
        }
      ],
      "metadata": {
        "limit": null,
        "offset": null,
        "total": 2,
        "sort_by": null,
        "sort_order": null
      },
      "errors": []
    }
    ```
*   **Verification**:
    *   `KPI_A_1` (`36be655e...`) is **Visible**
    *   `KPI_A_2` (`2636c38e...`) is **Visible**
    *   `KPI_B_1` is **NOT Visible**
    *   `KPI_B_2` is **NOT Visible**
*   **Status**: **PASS**

---

### Test 2: Authenticate as Tenant B
*   **Request**: `GET /api/v1/esg/frameworks/594c8317-c30b-4ce2-8ce1-0f80107deb8d/mappings?tenant_id=org_b_id`
*   **Headers**: `Authorization: Bearer <Tenant_B_Token>`
*   **API Response**:
    ```json
    {
      "success": true,
      "data": [
        {
          "id": "3fa57722-05bd-4515-9665-eaa9e379a4fd",
          "framework_id": "594c8317-c30b-4ce2-8ce1-0f80107deb8d",
          "kpi_definition_id": "3cc46797-9e7c-477f-9d00-a0e8c8d93aef",
          "framework_section": "Sec C",
          "framework_principle": null,
          "framework_question": "Q3",
          "reporting_category": "Mandatory",
          "created_at": "2026-06-16T14:36:08.900062"
        },
        {
          "id": "cb94bd62-f3ff-4d24-b8d6-e45e02d9509e",
          "framework_id": "594c8317-c30b-4ce2-8ce1-0f80107deb8d",
          "kpi_definition_id": "df2ecaee-4437-4aa2-be99-7eaf389a0c36",
          "framework_section": "Sec D",
          "framework_principle": null,
          "framework_question": "Q4",
          "reporting_category": "Mandatory",
          "created_at": "2026-06-16T14:36:08.900063"
        }
      ],
      "metadata": {
        "limit": null,
        "offset": null,
        "total": 2,
        "sort_by": null,
        "sort_order": null
      },
      "errors": []
    }
    ```
*   **Verification**:
    *   `KPI_B_1` (`3cc46797...`) is **Visible**
    *   `KPI_B_2` (`df2ecaee...`) is **Visible**
    *   `KPI_A_1` is **NOT Visible**
    *   `KPI_A_2` is **NOT Visible**
*   **Status**: **PASS**

---

### Test 3: Attempt Direct Access to Tenant B mappings via Tenant A token
*   **Request**: `GET /api/v1/esg/frameworks/594c8317-c30b-4ce2-8ce1-0f80107deb8d/mappings?tenant_id=org_b_id`
*   **Headers**: `Authorization: Bearer <Tenant_A_Token>` (Unauthorized context context probing)
*   **API Response**:
    ```json
    {
      "success": false,
      "data": null,
      "metadata": null,
      "errors": [
        {
          "code": "HTTP_ERROR",
          "message": "Resource not found"
        }
      ]
    }
    ```
*   **Verification**:
    *   Returns **`404 Not Found`** instead of `403 Forbidden` (anti-enumeration compliance).
    *   No tenant organization data is leaked.
    *   No framework mapping structure is leaked.
*   **Status**: **PASS**

---

## 3. Validation Results Summary

| Test Case | Description | Expected Status | Actual Status | Result |
| :--- | :--- | :--- | :--- | :--- |
| **Test 1** | Retrieve mappings authenticated as Tenant A | `200 OK` (Only Tenant A KPIs returned) | `200 OK` (Only Tenant A KPIs returned) | **PASS** |
| **Test 2** | Retrieve mappings authenticated as Tenant B | `200 OK` (Only Tenant B KPIs returned) | `200 OK` (Only Tenant B KPIs returned) | **PASS** |
| **Test 3** | Access Tenant B mappings context as Tenant A | `404 Not Found` (No details leaked) | `404 Not Found` (No details leaked) | **PASS** |

> [!IMPORTANT]
> The database queries on the dynamic `framework_mappings` join table filter mappings explicitly based on `EsgKpiDefinition.tenant_id == resolved_tenant_id`. Combined with active RBAC context checks (`get_tenant_context`), mappings remain fully tenant-isolated.
