# Sprint 3 Prompt 2 Report — Process Mining Engine

## 1. Files Created & Modified

### Created Files
*   `[ocel_parser.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/core/ocel_parser.py)`

### Modified Files
*   `[requirements.txt](file:///Users/rudrapratapsingh/Desktop/newpro/backend/requirements.txt)`
*   `[process_discovery_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/process_discovery_service.py)`
*   `[variant_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/variant_service.py)`
*   `[bottleneck_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/bottleneck_service.py)`
*   `[process_graph_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/process_graph_service.py)`
*   `[test_process_mining.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/tests/test_process_mining.py)`

---

## 2. PM4Py Integration & Miner Selection

*   **Libraries used:** `pm4py`, `pandas` (configured in requirements.txt and loaded in venv).
*   **Miner selected:** 
    *   **Inductive Miner** (`pm4py.discover_process_tree`) is selected if unique activities count < 20.
    *   **Heuristics Miner** (`pm4py.discover_heuristics_net`) is selected for denser activity logs.

---

## 3. Services Implemented

*   `parse_dataset_to_dataframe`: Converts CSV log lines into PM4Py compliant DataFrames; parses dates; extracts optional object type metadata (`object_id`, `object_type`).
*   `ProcessDiscoveryService.trigger_discovery`: Selects miner, discovers DFG, calculates throughput time, and saves model records, variant lists, bottleneck delay nodes, and graph models.
*   `VariantService.generate_and_save_variants`: Groups chronological paths by Case ID, computes frequencies/percentages, and saves variants.
*   `BottleneckService.generate_and_save_bottlenecks`: Extracts transition timing delays, counts loop repetitions, and identifies slowest transitions.
*   `ProcessGraphService.generate_and_save_graphs`: Compiles node list, transition edge list, and counts from dfg results.

---

## 4. Summary Metrics Generated

*   `total_events`: Count of rows in dataset.
*   `total_cases`: Count of unique cases.
*   `total_activities`: Count of unique activity names.
*   `average_case_length`: Average events per case.
*   `average_throughput_time`: Average elapsed time between first and last event timestamps per case (in seconds).

---

## 5. Validation Results

*   **Automated tests run:** `test_process_discovery_lifecycle` executes full pipeline and checks persistence states.
*   **Result status:** Passed.

---

## 6. Known Issues & Blockers Before Prompt 3

*   **Known Issues:** None.
*   **Blockers:** None.
