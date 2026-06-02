#!/usr/bin/env python3
"""Plot median query runtime by threshold from a processed benchmark CSV."""

from __future__ import annotations

import argparse
import csv
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TypeAlias

# Type aliases for clarity
QueryName: TypeAlias = str
Threshold: TypeAlias = int
MeasuredTime: TypeAlias = float


def load_measurements(csv_path: Path) -> Dict[QueryName, Dict[Threshold, List[MeasuredTime]]]:
    measurements: Dict[QueryName, Dict[Threshold, List[MeasuredTime]]] = {}

    with csv_path.open(newline='', encoding='utf-8') as handle:
        reader = csv.reader(handle)

        for row in reader:
            if len(row) < 4:
                continue

            query_name = row[0].strip()
            threshold_raw = row[1].strip()
            time_raw = row[3].strip()

            if query_name == '' or threshold_raw == '' or time_raw == '':
                continue

            try:
                threshold = int(threshold_raw)
            except ValueError as exc:
                raise ValueError(f"Unable to parse threshold value {threshold_raw!r}") from exc

            try:
                time_value = float(time_raw)
            except ValueError as exc:
                raise ValueError(f"Unable to parse runtime value {time_raw!r}") from exc

            measurements.setdefault(query_name, {}).setdefault(threshold, []).append(time_value)

    return measurements


def compute_medians(measurements: Dict[QueryName, Dict[Threshold, List[MeasuredTime]]]) -> Dict[QueryName, Dict[Threshold, MeasuredTime]]:
    medians: Dict[QueryName, Dict[Threshold, MeasuredTime]] = {}
    for query_name, threshold_map in measurements.items():
        medians[query_name] = {
            threshold: statistics.median(values)
            for threshold, values in threshold_map.items()
        }
    return medians


def compute_confidence_intervals(
    measurements: Dict[Threshold, List[MeasuredTime]], confidence: float = 0.95
) -> Dict[Threshold, Tuple[MeasuredTime, MeasuredTime]]:
    """Compute 95% confidence intervals for each threshold using t-distribution.
    
    Args:
        measurements: dict mapping threshold to list of measured values
        confidence: confidence level (default 0.95 for 95% CI)
    
    Returns:
        dict mapping threshold to (lower_bound, upper_bound)
    """
    try:
        from scipy import stats
    except ImportError:
        raise ImportError(
            "scipy is required for confidence interval computation. "
            "Install it with 'pip install scipy'."
        )
    
    cis: Dict[Threshold, Tuple[MeasuredTime, MeasuredTime]] = {}
    alpha = 1.0 - confidence
    
    for threshold, values in measurements.items():
        if len(values) < 2:
            # Not enough data for CI
            cis[threshold] = (values[0], values[0])
            continue
        
        mean = statistics.mean(values)
        sem = statistics.stdev(values) / (len(values) ** 0.5)  # standard error of mean
        df = len(values) - 1
        t_crit = stats.t.ppf(1 - alpha / 2, df)
        margin = t_crit * sem
        # print(f"Threshold {threshold}: mean={mean:.4f}, sem={sem:.4f}, t_crit={t_crit:.4f}, margin={margin:.4f}")
        
        cis[threshold] = (mean - margin, mean + margin)
    
    return cis


def plot_query_mean(
    query_name: QueryName,
    means: Dict[Threshold, MeasuredTime],
    confidence_intervals: Optional[Dict[Threshold, Tuple[MeasuredTime, MeasuredTime]]] = None,
    output_path: Optional[Path] = None,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "matplotlib is required to plot results. Install it with 'pip install matplotlib'."
        ) from exc

    thresholds = sorted(means)
    times_mean = [means[t] for t in thresholds]

    # Prepare error bars if confidence intervals provided
    errors = None

    if confidence_intervals:
        lower = [confidence_intervals[t][0] for t in thresholds]
        upper = [confidence_intervals[t][1] for t in thresholds]
        # print(f"lower bounds: {lower}")
        # print(f"upper bounds: {upper}")
        # print(f"times: {times_mean}")
        errors = [times_mean[i] - lower[i] for i in range(len(times_mean))], \
                 [upper[i] - times_mean[i] for i in range(len(times_mean))]
        # print(f"errors: {errors}")

    plt.figure(figsize=(10, 6))
    if errors:
        plt.errorbar(thresholds, times_mean, yerr=errors, marker='o', linestyle='-', capsize=5, capthick=2)
        plt.title(f"Mean runtime for query '{query_name}' (with 95% CI)")
    else:
        plt.plot(thresholds, times_mean, marker='o', linestyle='-')
        plt.title(f"Mean runtime for query '{query_name}'")
    
    plt.xlabel('Threshold')
    plt.ylabel('Mean runtime (s)')
    plt.grid(True, linestyle='--', alpha=0.4)
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=200)
        print(f"Saved plot to {output_path}")
    else:
        plt.show()

def plot_query_median(
    query_name: QueryName,
    medians: Dict[Threshold, MeasuredTime],
    output_path: Optional[Path] = None,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "matplotlib is required to plot results. Install it with 'pip install matplotlib'."
        ) from exc

    thresholds = sorted(medians)
    times_median = [medians[t] for t in thresholds]


    plt.figure(figsize=(10, 6))
    
    plt.plot(thresholds, times_median, marker='o', linestyle='-')
    plt.title(f"Median runtime for query '{query_name}'")
    
    plt.xlabel('Threshold')
    plt.ylabel('Median runtime (s)')
    plt.grid(True, linestyle='--', alpha=0.4)
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=200)
        print(f"Saved plot to {output_path}")
    else:
        plt.show()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description='Read out_benchmark_processed.csv and plot median runtime by threshold for a given query.'
    )
    parser.add_argument(
        'query',
        help='Query name to plot (basename without .sql)'
    )
    parser.add_argument(
        '--csv',
        default='out_benchmark_processed.csv',
        help='Path to the processed benchmark CSV file'
    )
    parser.add_argument(
        '--save',
        metavar='IMAGE',
        help='Save the plot to a file instead of showing it interactively'
    )

    args = parser.parse_args(argv)
    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise FileNotFoundError(f"Benchmark CSV file not found: {csv_path}")

    measurements = load_measurements(csv_path)
    medians = compute_medians(measurements)
    means = {
        query_name: {
            threshold: statistics.mean(values)
            for threshold, values in threshold_map.items()
        }
        for query_name, threshold_map in measurements.items()
    }

    if args.query not in medians:
        available = ', '.join(sorted(medians.keys()))
        raise ValueError(
            f"Query '{args.query}' not found in {csv_path}. Available queries: {available}"
        )

    # Compute confidence intervals for the selected query
    cis = compute_confidence_intervals(measurements[args.query])
    
    plot_query_mean(
        args.query,
        means[args.query],
        confidence_intervals=cis,
        output_path=Path(args.save).with_suffix('.mean.png') if args.save else None,
    )
    plot_query_median(
        args.query,
        medians[args.query],
        output_path=Path(args.save).with_suffix('.median.png') if args.save else None,
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

# 13, 15, 19!, 22!, 23!, 24!!