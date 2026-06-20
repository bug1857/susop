import csv
import re
from typing import List, Dict, Any, Tuple

def detect_delimiter(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            sample = f.read(2048)
            if not sample:
                return ","
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=[",", ";", "\t", "|"])
            return dialect.delimiter
    except Exception:
        return ","

def validate_csv(file_path: str, delimiter: str) -> Tuple[List[str], List[Dict[str, Any]], int]:
    errors = []
    headers = []
    row_count = 0
    
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=delimiter)
            try:
                headers = next(reader)
            except StopIteration:
                errors.append({"row": 0, "error": "CSV file is empty"})
                return [], errors, 0

            # Strip spaces from headers
            headers = [h.strip() for h in headers]

            # Check for empty headers
            for idx, h in enumerate(headers):
                if not h:
                    errors.append({"row": 0, "error": f"Empty header label at column index {idx}"})

            # Check for duplicate headers
            seen_headers = set()
            for h in headers:
                if h:
                    if h in seen_headers:
                        errors.append({"row": 0, "error": f"Duplicate header column label found: '{h}'"})
                    seen_headers.add(h)

            expected_len = len(headers)
            for idx, row in enumerate(reader, start=1):
                row_count += 1
                # Check column count consistency
                if len(row) != expected_len:
                    errors.append({
                        "row": idx,
                        "error": f"Row has inconsistent column count (expected {expected_len}, got {len(row)})"
                    })
                # Check for empty rows
                if not any(val.strip() for val in row):
                    errors.append({"row": idx, "error": "Row is entirely blank"})
                    
    except UnicodeDecodeError:
        errors.append({"row": 0, "error": "File encoding mismatch (must be UTF-8)"})
    except Exception as e:
        errors.append({"row": 0, "error": f"Failed parsing CSV structure: {str(e)}"})

    return headers, errors, row_count

def detect_schema(headers: List[str]) -> Dict[str, Any]:
    suggestions = {}
    
    patterns = {
        "event_id": (r"(event_?id|uuid|id)", 0.95),
        "case_id": (r"(case_?id|order_?id|process_?id|id_case|order_no)", 0.90),
        "activity": (r"(activity|task|step|action|concept:name)", 0.95),
        "timestamp": (r"(time|date|timestamp|created_?at|occurred_?at)", 0.95),
        "object_ids": (r"(object_?id|items|batch_?id|product_?id)", 0.85),
        "supplier_id": (r"(supplier|vendor|supplier_?id|vendor_?id|partner)", 0.90),
        "carbon_fields": (r"(co2|emissions?|carbon|co2e|greenhouse|ghg)", 0.90),
        "transport_fields": (r"(transport|logistics|mode|freight|transit|route)", 0.85),
        "esg_fields": (r"(water|waste|esg|energy|electricity|safety|social)", 0.80),
        "violation_fields": (r"(violation|deviation|error|breach|alert|non_?conformance)", 0.85)
    }

    for header in headers:
        clean_header = header.lower().strip()
        matched_role = None
        max_confidence = 0.0
        
        for role, (regex, confidence) in patterns.items():
            if re.search(regex, clean_header):
                if confidence > max_confidence:
                    max_confidence = confidence
                    matched_role = role
                    
        if matched_role:
            suggestions[header] = {
                "role": matched_role,
                "confidence": max_confidence
            }
            
    return suggestions
