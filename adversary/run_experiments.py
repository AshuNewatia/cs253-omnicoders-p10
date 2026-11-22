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
    subprocess.run([str(item) for item in cmd], check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", default="100,200,400,800,1600,3200")
    parser.add_argument("--seeds", default="12345,2026,7",
                        help="comma-separated seeds; used for random pattern")
    args = parser.parse_args()
  try:
    sizes = [int(value.strip()) for value in args.sizes.split(",") if value.strip()]
    seeds = [int(value.strip()) for value in args.seeds.split(",") if value.strip()]
  except ValueError:
              parser.error("sizes and seeds must contain comma-separated integers")
    if not sizes or any(size < 2 for size in sizes):
        parser.error("provide atleast one size , and all sizes must be >= 2")
    if not seeds:
        parser.error("at least one seed is required ")

    RESULTS.mkdir(parents=True , exist_ok=True)
    executable_suffix = ".exe" if sys.platform == "win32" else ""
   generator = ADV / f"adversary{executable_suffix}"
    benchmark_a = ADV / f"heap_benchmark_A{executable_suffix}"
    benchmark_b = ADV / f"heap_benchmark_B{executable_suffix}"
    compiler = "g++"
    common_flags = [compiler, "-std=c++17", "-O2", "-Wall", "-Wextra", "-pedantic", "-DD5_COUNT_COMPARISONS"]
    run(common_flags + [ADV / "Adversary.cpp", "-o", generator])
    run(common_flags + ["-DTEST_STRUCTURE_A", ADV / "D5_HeapBenchmark.cpp", "-o", benchmark_a])
    run(common_flags + [ADV / "D5_HeapBenchmark.cpp", "-o", benchmark_b])

    output = RESULTS / "d5_experiment_results.csv"
    summary = RESULTS / "d5_worst_patterns.csv"
    fields = ["structure", "pattern", "seed", "n", "build_comparisons",
              "extract_comparisons", "extract_comparisons_per_nlog2n"]
    rows = []
    for n in sizes:
        for pattern in PATTERNS:
            pattern_seeds = seeds if pattern == "random" else [seeds[0]]
            for seed in pattern_seeds:
                csv_path = ADV / f"input_{n}_{pattern}_{seed}.csv"
            try:
                with csv_path.open("w", newline="") as csv_file:
                    run([generator, n, pattern, seed], stdout=csv_file)
                for structure, executable in (("A", benchmark_a), ("B", benchmark_b)):
                    result = subprocess.run([str(executable), str(csv_path)], check=True,
                                             capture_output=True, text=True)
                    parsed_rows = list(csv.DictReader(result.stdout.splitlines()))
                            if len(parsed_rows) != 1:
                                        raise RuntimeError(f"unexpected benchmark output for structure {structure}:"f"expected one data row, got {len(parsed_rows)}")
                                        parsed = parsed_rows[0]
                    comparisons = int(parsed["extract_comparisons"])
                    rows.append({
                        "structure": structure, "pattern": pattern, "seed": seed,
                        "n": n, "build_comparisons": int(parsed["build_comparisons"]),
                        "extract_comparisons": comparisons,
                        "extract_comparisons_per_nlog2n":
                            f"{comparisons / (n * math.log2(n)):.6f}"
                                ),
                    })
            finally:
               if csv_path.exists():csv_path.unlink()
                print(f"completed n={n}, pattern={pattern}, seed={seed}")

    with output.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

size_average = {}
for row in rows:
            key = (row["structure"],row["pattern"],row["n"] )
            size_averages.setdefault(key,[]).append(int(row["extract_comparisions"]))
          pattern_averages = {}
          for (structure, pattern,_n), values in size_averages.items():
              
               pattern_key = (structure , pattern)
               pattern_averages.setdefault(pattern_key,[]).append(sum(values)/len(values))
with summary.open("w", newline="") as csv_file:
       writer = csv.writer(csv_file)
       writer.writerow(["structure","pattern","average_extraction_comparisons"])

    for structure in ("A", "B"):

        ranked = []

        for (item_structure, pattern), values in pattern_averages.items():

            if item_structure == structure:
                ranked.append((pattern, sum(values) / len(values)))

        ranked.sort(key=lambda item: item[1], reverse=True)

        for pattern, average in ranked:
            writer.writerow([
                structure,
                pattern,
                f"{average:.2f}"
            ])
    print("\nExperiments completed successfully.")
    print(f"\nResults written to: {output}")
    print(f"Pattern ranking written to: {summary}")

if __name__ == "__main__":
    main()
