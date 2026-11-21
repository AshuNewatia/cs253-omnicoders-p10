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
PATTERNS = ["ascending", "descending", "alternating", "sawtooth",
            "bit-reversal", "random", "equal-reverse-arrival"]


def run(cmd, **kwargs):
    subprocess.run([str(x) for x in cmd], check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", default="100,200,400,800,1600,3200")
    parser.add_argument("--seeds", default="12345,2026,7",
                        help="comma-separated seeds; used for random pattern")
    args = parser.parse_args()
    sizes = [int(x) for x in args.sizes.split(",")]
    seeds = [int(x) for x in args.seeds.split(",")]
    if any(n < 2 for n in sizes):
        parser.error("all sizes must be >= 2")

    RESULTS.mkdir(exist_ok=True)
    generator = ADV / ("adversary.exe" if sys.platform == "win32" else "adversary")
    bench_a = ADV / ("heap_benchmark_A.exe" if sys.platform == "win32" else "heap_benchmark_A")
    bench_b = ADV / ("heap_benchmark_B.exe" if sys.platform == "win32" else "heap_benchmark_B")
    cxx = "g++"
    common = [cxx, "-std=c++17", "-O2", "-Wall", "-Wextra", "-pedantic", "-DD5_COUNT_COMPARISONS"]
    run(common + [ADV / "Adversary.cpp", "-o", generator])
    run(common + ["-DTEST_STRUCTURE_A", ADV / "D5_HeapBenchmark.cpp", "-o", bench_a])
    run(common + [ADV / "D5_HeapBenchmark.cpp", "-o", bench_b])

    output = RESULTS / "d5_experiment_results.csv"
    fields = ["structure", "pattern", "seed", "n", "build_comparisons",
              "extract_comparisons", "extract_comparisons_per_nlog2n"]
    rows = []
    for n in sizes:
        for pattern in PATTERNS:
            use_seeds = seeds if pattern == "random" else [seeds[0]]
            for seed in use_seeds:
                csv_path = ADV / f"input_{n}_{pattern}_{seed}.csv"
                with csv_path.open("w", newline="") as f:
                    run([generator, n, pattern, seed], stdout=f)
                for structure, exe in (("A", bench_a), ("B", bench_b)):
                    result = subprocess.run([str(exe), str(csv_path)], check=True,
                                             capture_output=True, text=True)
                    parsed = list(csv.DictReader(result.stdout.splitlines()))[0]
                    comparisons = int(parsed["extract_comparisons"])
                    rows.append({
                        "structure": structure, "pattern": pattern, "seed": seed,
                        "n": n, "build_comparisons": int(parsed["build_comparisons"]),
                        "extract_comparisons": comparisons,
                        "extract_comparisons_per_nlog2n":
                            f"{comparisons / (n * math.log2(n)):.6f}"
                    })
                csv_path.unlink(missing_ok=True)
                print(f"completed n={n}, pattern={pattern}, seed={seed}")

    with output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

summary = RESULTS / "d5_worst_patterns.csv"

with summary.open("w", newline="") as f:
    writer = csv.writer(f)

    writer.writerow([
        "structure",
        "pattern",
        "average_extraction_comparisons"
    ])

    averages = {}

    for row in rows:
        key = (row["structure"], row["pattern"])

        if key not in averages:
            averages[key] = []

        averages[key].append(row["extract_comparisons"])

    for structure in ("A", "B"):

        ranked = []

        for (s, pattern), values in averages.items():

            if s == structure:
                average = sum(values) / len(values)
                ranked.append((pattern, average))

        ranked.sort(key=lambda x: x[1], reverse=True)

        for pattern, average in ranked:
            writer.writerow([
                structure,
                pattern,
                f"{average:.2f}"
            ])

    print(f"\nResults written to: {output}")
    print(f"Pattern ranking written to: {summary}")

if __name__ == "__main__":
    main()
