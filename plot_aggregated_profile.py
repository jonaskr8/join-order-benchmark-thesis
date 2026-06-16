#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import List, Tuple, Optional


def load_aggregated_profile(csv_path: Path) -> Tuple[List[int], List[float], List[float]]:
    thresholds: List[int] = []
    optimizer_times: List[float] = []
    join_times: List[float] = []

    with csv_path.open(newline='', encoding='utf-8') as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 3:
                print(f"Warning: Skipping malformed row in {csv_path}: {row}")
                continue

            try:
                threshold = int(row[0].strip())
                optimizer_timing = float(row[1].strip())
                sum_joins = float(row[2].strip())
            except ValueError:
                print(f"Warning: Skipping row with invalid data in {csv_path}: {row}")
                continue

            thresholds.append(threshold)
            optimizer_times.append(optimizer_timing)
            join_times.append(sum_joins)

    sorted_data = sorted(zip(thresholds, optimizer_times, join_times), key=lambda item: item[0])
    if not sorted_data:
        raise ValueError(f"No valid data found in {csv_path}")

    thresholds, optimizer_times, join_times = map(list, zip(*sorted_data))
    return thresholds, optimizer_times, join_times


def plot_aggregated_profile(
    thresholds: List[int],
    optimizer_times: List[float],
    join_times: List[float],
    output_path: Optional[Path] = None,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "matplotlib is required to plot results. Install it with 'pip install matplotlib'."
        ) from exc

    plt.figure(figsize=(10, 6))
    plt.stackplot(
        thresholds,
        optimizer_times,
        join_times,
        labels=['Planning time', 'Join time'],
        colors=['#4c72b0', '#dd8452'],
        alpha=0.8,
    )
    plt.plot(
        thresholds,
        [o + j for o, j in zip(optimizer_times, join_times)],
        color='black',
        linewidth=1.2,
        linestyle='--',
        label='Total time',
    )

    plt.title('Aggregated profiling time by threshold')
    plt.xlabel('Threshold')
    plt.ylabel('Time (seconds)')
    plt.legend(loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=200)
        print(f"Saved plot to {output_path}")
        plt.close()
    else:
        plt.show()


def plot_aggregated_profile_speedup(
    thresholds: List[int],
    optimizer_times: List[float],
    join_times: List[float],
    output_path: Optional[Path] = None,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "matplotlib is required to plot results. Install it with 'pip install matplotlib'."
        ) from exc

    if not join_times:
        raise ValueError("No join time data available for speedup plot")

    # Choose baseline as the join time at threshold == 12 (if present)
    baseline_threshold = 12
    try:
        idx = thresholds.index(baseline_threshold)
        baseline = join_times[idx]
    except ValueError:
        print(f"Warning: baseline threshold {baseline_threshold} not found; falling back to first threshold")
        baseline = join_times[0]
    # speedup = baseline / current_join_time
    speedup = [baseline / jt if jt > 0 else float('nan') for jt in join_times]

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.plot(
        thresholds,
        speedup,
        marker='o',
        linestyle='-',
        color='#2ca02c',
        label='Speedup (baseline / join_time)'
    )
    ax1.set_xlabel('Threshold')
    ax1.set_ylabel('Relative speedup', color='#2ca02c')
    ax1.tick_params(axis='y', labelcolor='#2ca02c')
    ax1.grid(True, linestyle='--', alpha=0.3)

    # Show planning time on a secondary axis to correlate planning cost
    ax2 = ax1.twinx()
    ax2.plot(
        thresholds,
        optimizer_times,
        color='#4c72b0',
        marker='x',
        linestyle='--',
        label='Planning time (s)'
    )
    ax2.set_ylabel('Planning time (seconds)', color='#4c72b0')
    ax2.tick_params(axis='y', labelcolor='#4c72b0')

    fig.suptitle('Relative speedup of join execution vs. planning time')
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    fig.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=200)
        print(f"Saved plot to {output_path}")
        plt.close(fig)
    else:
        plt.show()


def plot_aggregated_profile_payoff(
    thresholds: List[int],
    optimizer_times: List[float],
    join_times: List[float],
    output_path: Optional[Path] = None,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "matplotlib is required to plot results. Install it with 'pip install matplotlib'."
        ) from exc

    if not join_times or not optimizer_times:
        raise ValueError("Insufficient data for payoff plot")

    # Use baseline threshold == 12 for payoff calculation
    baseline_threshold = 12
    try:
        bidx = thresholds.index(baseline_threshold)
        baseline_join = join_times[bidx]
        baseline_optimizer = optimizer_times[bidx]
    except ValueError:
        print(f"Warning: payoff baseline threshold {baseline_threshold} not found; using first threshold as baseline")
        baseline_join = join_times[0]
        baseline_optimizer = optimizer_times[0]

    payoff = []
    for jt, ot in zip(join_times, optimizer_times):
        denom = ot - baseline_optimizer
        if denom == 0:
            payoff.append(0)
        else:
            payoff.append((baseline_join - jt) / denom)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(thresholds, payoff, marker='o', linestyle='-', color='#9467bd', label='Seconds saved per extra planning second')
    ax.set_xlabel('Threshold')
    ax.set_ylabel('Seconds saved per extra planning second')
    ax.grid(True, linestyle='--', alpha=0.3)

    # Also show planning time for context on a secondary axis
    ax2 = ax.twinx()
    ax2.plot(thresholds, optimizer_times, color='#4c72b0', marker='x', linestyle='--', label='Planning time (s)')
    ax2.set_ylabel('Planning time (seconds)', color='#4c72b0')
    ax2.tick_params(axis='y', labelcolor='#4c72b0')

    fig.suptitle(f'Payoff per extra planning second (baseline threshold={baseline_threshold})')
    ax.legend(loc='upper left')
    ax2.legend(loc='upper right')
    fig.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=200)
        print(f"Saved plot to {output_path}")
        plt.close(fig)
    else:
        plt.show()


def plot_aggregated_profile_log(
    thresholds: List[int],
    optimizer_times: List[float],
    join_times: List[float],
    output_path: Optional[Path] = None,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "matplotlib is required to plot results. Install it with 'pip install matplotlib'."
        ) from exc

    plt.figure(figsize=(10, 6))
    plt.stackplot(
        thresholds,
        optimizer_times,
        join_times,
        labels=['Planning time', 'Join time'],
        colors=['#4c72b0', '#dd8452'],
        alpha=0.8,
    )
    plt.plot(
        thresholds,
        [o + j for o, j in zip(optimizer_times, join_times)],
        color='black',
        linewidth=1.2,
        linestyle='--',
        label='Total time',
    )

    plt.yscale('log')
    plt.title('Aggregated profiling time by threshold (log scale)')
    plt.xlabel('Threshold')
    plt.ylabel('Time (seconds, log scale)')
    plt.legend(loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.3, which='both')
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=200)
        print(f"Saved plot to {output_path}")
        plt.close()
    else:
        plt.show()


def plot_aggregated_profile_secondary_axis(
    thresholds: List[int],
    optimizer_times: List[float],
    join_times: List[float],
    output_path: Optional[Path] = None,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "matplotlib is required to plot results. Install it with 'pip install matplotlib'."
        ) from exc

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.plot(
        thresholds,
        join_times,
        color='#dd8452',
        marker='o',
        linestyle='-',
        label='Join time',
    )
    ax1.set_xlabel('Threshold')
    ax1.set_ylabel('Join time (seconds)', color='#dd8452')
    ax1.tick_params(axis='y', labelcolor='#dd8452')
    ax1.set_ylim(bottom=0, top=max(join_times) * 1.2)
    ax1.grid(True, linestyle='--', alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(
        thresholds,
        optimizer_times,
        color='#4c72b0',
        marker='x',
        linestyle='--',
        label='Planning time',
    )
    ax2.set_ylabel('Planning time (seconds)', color='#4c72b0')
    ax2.tick_params(axis='y', labelcolor='#4c72b0')
    ax2.set_ylim(bottom=0, top=max(optimizer_times) * 1.2)
    fig.suptitle('Aggregated profiling time by threshold (secondary axis)')
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    fig.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=200)
        print(f"Saved plot to {output_path}")
        plt.close(fig)
    else:
        plt.show()


def plot_aggregated_profile_normalized(
    thresholds: List[int],
    optimizer_times: List[float],
    join_times: List[float],
    output_path: Optional[Path] = None,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "matplotlib is required to plot results. Install it with 'pip install matplotlib'."
        ) from exc

    max_optimizer = max(optimizer_times) if optimizer_times else 1.0
    max_join = max(join_times) if join_times else 1.0
    normalized_optimizer = [t / max_optimizer for t in optimizer_times]
    normalized_join = [t / max_join for t in join_times]

    plt.figure(figsize=(10, 6))
    plt.stackplot(
        thresholds,
        normalized_optimizer,
        normalized_join,
        labels=['Planning time (normalized)', 'Join time (normalized)'],
        colors=['#4c72b0', '#dd8452'],
        alpha=0.8,
    )
    plt.plot(
        thresholds,
        [o + j for o, j in zip(normalized_optimizer, normalized_join)],
        color='black',
        linewidth=1.2,
        linestyle='--',
        label='Normalized total',
    )

    plt.title('Aggregated profiling time by threshold (normalized)')
    plt.xlabel('Threshold')
    plt.ylabel('Normalized time')
    plt.legend(loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=200)
        print(f"Saved plot to {output_path}")
        plt.close()
    else:
        plt.show()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description='Plot aggregated profiling times from profiling_results_aggregated.csv.'
    )
    parser.add_argument(
        'csv',
        nargs='?', 
        default='profiling/profiling_results_aggregated_all.csv',
        help='Path to profiling_results_aggregated.csv',
    )
    parser.add_argument(
        '--save',
        metavar='PREFIX',
        help='Save the plots to image files using the given prefix',
    )

    args = parser.parse_args(argv)
    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    thresholds, optimizer_times, join_times = load_aggregated_profile(csv_path)
    if args.save:
        save_prefix = Path(args.save)
        if save_prefix.suffix:
            save_prefix = save_prefix.with_suffix('')
        paths = {
            'default': save_prefix.with_suffix('.area.png'),
            'log': save_prefix.with_suffix('.log.png'),
            'secondary': save_prefix.with_suffix('.secondary.png'),
            'normalized': save_prefix.with_suffix('.normalized.png'),
            'speedup': save_prefix.with_suffix('.speedup.png'),
            'payoff': save_prefix.with_suffix('.payoff.png'),
        }
    else:
        paths = {
            'default': None,
            'log': None,
            'secondary': None,
            'normalized': None,
            'speedup': None,
            'payoff': None,
        }

    plot_aggregated_profile(thresholds, optimizer_times, join_times, output_path=paths['default'])
    plot_aggregated_profile_log(thresholds, optimizer_times, join_times, output_path=paths['log'])
    plot_aggregated_profile_secondary_axis(thresholds, optimizer_times, join_times, output_path=paths['secondary'])
    plot_aggregated_profile_normalized(thresholds, optimizer_times, join_times, output_path=paths['normalized'])
    plot_aggregated_profile_speedup(thresholds, optimizer_times, join_times, output_path=paths['speedup'])
    plot_aggregated_profile_payoff(thresholds, optimizer_times, join_times, output_path=paths['payoff'])

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
