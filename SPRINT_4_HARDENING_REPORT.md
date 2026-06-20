# Sprint 4 — Final Hardening Report: Security & Performance Review

This report presents a thorough security, isolation, consistency, error handling, performance, indexing, and type-safety audit of the Sprint 4 implementation. 

---

## 1. Critical Issues
*No Critical (blocker/data-loss) issues detected in this sprint audit.*

---

## 2. High Issues

### Issue 1: Loop-Based Database Commits Causing Transaction Bottlenecks (N+1 Commits)
- **Location**:
  - `backend/app/services/conformance_service.py` (Line 281: `self.deviation_repo.create(dev)`)
  - `backend/app/services/carbon_attribution_service.py` (Line 94: `self.attr_repo.create(attr)`)
- **Impact**: For analyses with many execution traces and event sequences, inserting each deviation or attribution record commits individual transactions to SQLite/PostgreSQL in a loop. This leads to high write latency and scalability degradation.
- **Fix Recommendation**: 
  Implement a bulk creation method in the repositories (e.g. `DeviationRepository.create_all(list[ConformanceDeviation])`) that executes a single `db.add_all()` and a single `db.commit()` at the end of the check/attribution run.

### Issue 2: RangeError Crash on Invalid/Incomplete Date Selection
- **Location**:
  - `frontend/src/app/dashboard/conformance/page.tsx` (Line 305: `new Date(devStartDate).toISOString()`)
  - `frontend/src/app/dashboard/conformance/page.tsx` (Line 306: `new Date(devEndDate).toISOString()`)
- **Impact**: If a user enters an incomplete or malformed date string in the query filter input fields, calling `.toISOString()` directly on the parsed date throws an unhandled `RangeError: Invalid time value`, crashing the entire Next.js rendering engine.
- **Fix Recommendation**: 
  Validate the date string using a safe parser check or simple regex before invoking serialization, and wrap the `.toISOString()` call inside a try-catch block to handle errors gracefully without crashing the view.

---

## 3. Medium Issues

### Issue 3: TypeError Crash on Failed History List Responses
- **Location**:
  - `frontend/src/app/dashboard/conformance/page.tsx` (Line 228: `data.filter(...)`)
- **Impact**: If the backend returns an error envelope or an HTTP error status code (e.g. 401 Unauthorized or 404) instead of an array of analysis runs, calling `.filter()` directly on the JSON payload throws a `TypeError: data.filter is not a function`, leading to a page crash.
- **Fix Recommendation**: 
  Always verify that the response object is an array using `Array.isArray(data)` before applying filter/map array operations, and display a helpful empty state or alert banner on errors.

### Issue 4: Information Disclosure via Tenant ID Probing
- **Location**:
  - `backend/app/routers/conformance.py` (Lines 191, 237)
  - `backend/app/routers/process.py` (Line 80)
- **Impact**: A malicious user can probe model or analysis UUIDs belonging to other tenants. If they observe a `403 Forbidden` response instead of a `404 Not Found`, they obtain confirmation of the resource's existence in another tenant organization, representing a minor security leak.
- **Fix Recommendation**: 
  In the router validation checks, return a generic `404 Not Found` response if a resource is found but belongs to a different tenant organization, preventing external probing of database UUIDs.

---

## 4. Low Issues

### Issue 5: Missing Index on `parent_model_id` Foreign Key
- **Location**:
  - `backend/app/models/models.py` (Line 208)
- **Impact**: SQLite does not automatically index foreign key columns. Queries checking children or lineage version trees on `parent_model_id` will trigger full table scans, reducing query performance as reference model counts grow.
- **Fix Recommendation**: 
  Add `index=True` to the `parent_model_id` column definition in the `ReferenceModel` database model class.

### Issue 6: Auto-vanishing Success/Error Toast Banners
- **Location**:
  - `frontend/src/app/dashboard/conformance/page.tsx` (Lines 100-112)
- **Impact**: Important validation failures or success feedbacks vanish automatically after 4-5 seconds. If a user is distracted or looking elsewhere, they might miss critical alert details.
- **Fix Recommendation**: 
  Keep errors visible until the user explicitly dismisses them, or use a persistent notifications side-drawer.
