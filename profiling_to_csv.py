#!/usr/bin/env python3

import json
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ProfilingResult:
    threshold: int
    optimizer_timing: float
    sum_joins: float

def extract_join_timings(obj: Dict[str, Any], results: List[float]) -> List[float]:   
    # Check if current object is a JOIN operator
    if obj.get("operator_type") and "JOIN" in obj["operator_type"]:
        time = obj.get("operator_timing")
        if time is not None:
          results.append(float(time))
        else:
          print(f"Warning: JOIN operator found without operator_timing: {obj}")
    
    # Recursively check children
    for child in obj.get("children", []):
        extract_join_timings(child, results)
    
    return results


def extract_optimizer_timings(obj: Dict[str, Any]) -> Optional[float]:
    if obj.get("optimizer_join_order") is not None:
          return float(obj["optimizer_join_order"])
    return None

output_dir = Path("profiling")
output_dir.mkdir(exist_ok=True)
# output CSV file
output_file_per_query = output_dir / "profiling_results_per_query_all.csv"

all_results: List[ProfilingResult] = []
with open(output_file_per_query, "w") as o:
    # Process all JSON files
    def profile_sort_key(json_file: Path) -> tuple[str, int]:
        query_name, threshold_str = json_file.stem.rsplit("-", 1)
        return query_name, int(threshold_str)

    json_files = sorted(Path("profiling").glob("*.json"), key=profile_sort_key)
    for json_file in json_files:
        query_name, threshold_str = json_file.stem.rsplit("-", 1)
        threshold = int(threshold_str)

        with open(json_file) as f:
            data: Dict[str, Any] = json.load(f)
            joins: List[float] = extract_join_timings(data, [])
            optimizer_timing: Optional[float] = extract_optimizer_timings(data)
            if optimizer_timing is None:
                print(f"Warning: No optimizer_join_order found in {json_file}")
                continue
            sum_joins = sum(joins)
            result = ProfilingResult(threshold=threshold, optimizer_timing=optimizer_timing, sum_joins=sum_joins)
            all_results.append(result)
            o.write(f"{query_name},{result.threshold},{result.optimizer_timing},{result.sum_joins}\n")
output_file_aggregated = output_dir / "profiling_results_aggregated_all.csv"

optimizer_timings_by_threshold: Dict[int, float] = defaultdict(float)
join_timings_by_threshold: Dict[int, float] = defaultdict(float)

for result in all_results:
    optimizer_timings_by_threshold[result.threshold] += result.optimizer_timing
    join_timings_by_threshold[result.threshold] += result.sum_joins

if optimizer_timings_by_threshold:
    min_threshold = min(optimizer_timings_by_threshold)
    max_threshold = max(optimizer_timings_by_threshold)

    with open(output_file_aggregated, "w") as f:
        for threshold in range(min_threshold, max_threshold + 1):
            optimizer_timing = optimizer_timings_by_threshold.get(threshold, 0)
            sum_joins = join_timings_by_threshold.get(threshold, 0)
            f.write(f"{threshold},{optimizer_timing},{sum_joins}\n")
else:
    print("Warning: no profiling results to aggregate.")
for json_file in output_dir.glob("*.json"):
    json_file.unlink()