#!/usr/bin/env python3
"""Build the D5 tools and run reproducible extraction experiments."""

import argparse
import csv
import math
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ADV = ROOT / "adversary"
RESULTS = ROOT / "results"

PATTERNS = [
    "ascending",
    "descending",
    "alternating",
    "sawtooth",
    "bit-reversal",
    "random",
    "equal-reverse-arrival",
]


def run(cmd, **kwargs):
    subprocess.run(
        [str(item) for item in cmd],
        check=True,
        **kwargs
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--sizes",
        default="100,200,400,800,1600,3200"
    )

    parser.add_argument(
        "--seeds",
        default="12345,2026,7",
        help="Comma-separated seeds; used for random pattern"
    )

    args = parser.parse_args()

    # Parse input sizes and random seeds.
    try:
        sizes = [
            int(v.strip())
            for v in args.sizes.split(",")
            if v.strip()
        ]

        seeds = [
            int(v.strip())
            for v in args.seeds.split(",")
            if v.strip()
        ]

    except ValueError:
        parser.error(
            "sizes and seeds must contain comma-separated integers"
        )

    if not sizes or any(n < 2 for n in sizes):
        parser.error(
            "Provide at least one size, and all sizes must be >= 2"
        )

    if not seeds:
        parser.error("At least one seed is required")

    if any(seed < 0 for seed in seeds):
        parser.error("Seeds must be non-negative")

    RESULTS.mkdir(parents=True, exist_ok=True)

    suffix = ".exe" if sys.platform == "win32" else ""

    generator = ADV / f"adversary{suffix}"
    benchmark_a = ADV / f"heap_benchmark_A{suffix}"
    benchmark_b = ADV / f"heap_benchmark_B{suffix}"

    compiler = "g++"

    common_flags = [
        compiler,
        "-std=c++17",
        "-O2",
        "-Wall",
        "-Wextra",
        "-pedantic",
        "-DD5_COUNT_COMPARISONS",
    ]

    # Compile the adversarial input generator.
    print("Compiling adversary generator...")

    run(
        common_flags
        + [
            ADV / "Adversary.cpp",
            "-o",
            generator,
        ]
    )

    # Compile Structure A benchmark.
    print("Compiling Structure A benchmark...")

    run(
        common_flags
        + [
            "-DTEST_STRUCTURE_A",
            ADV / "D5_HeapBenchmark.cpp",
            "-o",
            benchmark_a,
        ]
    )

    # Compile Structure B benchmark.
    print("Compiling Structure B benchmark...")

    run(
        common_flags
        + [
            ADV / "D5_HeapBenchmark.cpp",
            "-o",
            benchmark_b,
        ]
    )

    output = RESULTS / "d5_experiment_results.csv"
    summary = RESULTS / "d5_worst_patterns.csv"

    fields = [
        "structure",
        "pattern",
        "seed",
        "n",
        "build_comparisons",
        "extract_comparisons",
        "extract_comparisons_per_nlog2n",
    ]

    rows = []

    # Run experiments for every size and pattern.
    for n in sizes:

        for pattern in PATTERNS:

            pattern_seeds = (
                seeds if pattern == "random"
                else [seeds[0]]
            )

            for seed in pattern_seeds:

                csv_path = ADV / (
                    f"input_{n}_{pattern}_{seed}.csv"
                )

                try:
                    # Generate adversarial input.
                    with csv_path.open(
                        "w",
                        newline=""
                    ) as csv_file:

                        run(
                            [
                                generator,
                                n,
                                pattern,
                                seed,
                            ],
                            stdout=csv_file
                        )

                    # Benchmark both structures.
                    for structure, executable in (
                        ("A", benchmark_a),
                        ("B", benchmark_b),
                    ):

                        result = subprocess.run(
                            [
                                str(executable),
                                str(csv_path),
                            ],
                            check=True,
                            capture_output=True,
                            text=True,
                        )

                        parsed_rows = list(
                            csv.DictReader(
                                result.stdout.splitlines()
                            )
                        )

                        if len(parsed_rows) != 1:
                            raise RuntimeError(
                                "Unexpected benchmark output "
                                f"for Structure {structure}: "
                                f"expected one data row, "
                                f"got {len(parsed_rows)}"
                            )

                        parsed = parsed_rows[0]

                        comparisons = int(
                            parsed["extract_comparisons"]
                        )

                        build_comparisons = int(
                            parsed["build_comparisons"]
                        )

                        rows.append({
                            "structure": structure,
                            "pattern": pattern,
                            "seed": seed,
                            "n": n,
                            "build_comparisons": build_comparisons,
                            "extract_comparisons": comparisons,
                            "extract_comparisons_per_nlog2n":
                                f"{comparisons / (n * math.log2(n)):.6f}",
                        })

                finally:
                    # Remove temporary generated input.
                    if csv_path.exists():
                        csv_path.unlink()

                print(
                    f"Completed n={n}, "
                    f"pattern={pattern}, seed={seed}"
                )

    # Save detailed experimental results.
    with output.open("w", newline="") as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fields
        )

        writer.writeheader()
        writer.writerows(rows)

    # Calculate average extraction comparisons.
    per_size = {}

    for row in rows:

        key = (
            row["structure"],
            row["pattern"],
            row["n"],
        )

        per_size.setdefault(key, []).append(
            row["extract_comparisons"]
        )

    # Average across seeds for each size and pattern.
    pattern_averages = {}

    for (structure, pattern, n), values in per_size.items():

        key = (structure, pattern)

        pattern_averages.setdefault(key, []).append(
            sum(values) / len(values)
        )

    # Save worst-pattern rankings.
    with summary.open("w", newline="") as csv_file:

        writer = csv.writer(csv_file)

        writer.writerow([
            "structure",
            "pattern",
            "average_extraction_comparisons",
        ])

        for structure in ("A", "B"):

            ranked = [
                (
                    pattern,
                    sum(values) / len(values)
                )
                for (item_structure, pattern), values
                in pattern_averages.items()
                if item_structure == structure
            ]

            ranked.sort(
                key=lambda item: item[1],
                reverse=True
            )

            for pattern, average in ranked:

                writer.writerow([
                    structure,
                    pattern,
                    f"{average:.2f}",
                ])

    print("\nExperiments completed successfully.")
    print(f"Results written to: {output}")
    print(f"Pattern ranking written to: {summary}")


if __name__ == "__main__":
    main()
