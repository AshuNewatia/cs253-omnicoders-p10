# D5 — Adversary Contribution

## Overview

This folder contains the D5 adversary contribution for the OmniCoders CS253 project. Its purpose is to generate structured inputs for the team's priority-queue implementations, measure heap build and extraction comparisons, and document the mathematical lower-bound argument and experimental findings.

The D5 work evaluates **Structure A** and **Structure B** using the same generated patient inputs. It does not replace or claim ownership of either structure.

## Scope and deliverables

| File | Purpose |
|---|---|
| `Adversary.cpp` | Generates patient CSV inputs for the adversarial patterns listed below. |
| `D5_HeapBenchmark.cpp` | Builds and drains one selected heap while recording build and extraction comparisons. |
| `run_experiments.py` | Compiles the generator and both benchmark variants, runs the experiment matrix, and writes result CSV files. |
| `Report.md` | D5 proof, methodology, recorded results, interpretation, and limitations. |
| `D5_experiment_result.csv` / `d5_worst_patterns.csv` | D5 measurement and pattern-summary files, where included in the project snapshot. |

The benchmark includes the team's Structure A and Structure B source files by relative path. Those implementation files must be present in the full project repository for the benchmark to compile.

## Adversarial input patterns

The generator supports seven patterns:

- `ascending` — increasing priority ranks.
- `descending` — decreasing priority ranks.
- `alternating` — alternates low and high ranks.
- `sawtooth` — repeated local rises and falls.
- `bit-reversal` — rank order based on reversed binary index bits.
- `random` — seeded shuffle of distinct priority ranks.
- `equal-reverse-arrival` — equal priority values with reverse arrival order to stress comparator tie-breaking.

Each generated CSV uses this header:

```csv
id,severity,arrival_time,priority_key
```

Patient IDs are unique. The first six patterns use distinct priority keys. `equal-reverse-arrival` is a tie-breaking stress case and is not a distinct-key input for the lower-bound argument.

## Requirements

- Python 3
- A C++17-compatible `g++` compiler
- The full project repository, including:
  - `src/structA/structure_A.cpp`
  - `src/structB/structureB.cpp`
  - `app/ITriageQueue.h` and any headers/source files those implementations require

Run commands from the **repository root**, not from inside the `adversary` directory.

## Reproduce the experiments

Run the default experiment matrix:

```bash
python adversary/run_experiments.py
```

The default configuration uses input sizes `100,200,400,800,1600,3200` and seeds `12345,2026,7`. The script applies all three seeds to `random`; deterministic patterns use the first seed because their generated order does not depend on the seed.

To run a smaller experiment:

```bash
python adversary/run_experiments.py --sizes 100,200,400 --seeds 12345,2026
```

The runner compiles the generator and both benchmark variants with C++17, optimization, warnings, and D5 comparison instrumentation. It then generates each input, runs both structures, and writes the measurements.

### Output files

The experiment runner writes:

- `results/d5_experiment_results.csv` — one row per structure, pattern, size, and applicable seed. It includes build comparisons, extraction comparisons, and extraction comparisons normalized by `n log2(n)`.
- `results/d5_worst_patterns.csv` — aggregate extraction-comparison ranking by structure and pattern.

Temporary generated input CSV files are removed after each case. The benchmark checks that extraction returns priority keys in nondecreasing order.

## Mathematical result

The D5 report gives an existence proof for the comparison-based binary-heap extraction lower bound. Assuming linear-time heap construction and correct repeated minimum extraction, a heap that extracted every input using `o(n log n)` comparisons would yield a comparison sort faster than the `Omega(n log n)` sorting lower bound. Therefore, for every such implementation, at least one distinct-key input requires `Omega(n log n)` total extraction comparisons.

This is an existence result. It does **not** establish that one particular generated pattern is universally worst-case for every implementation.

## How to interpret the measurements

- The experiments compare the current versions of Structure A and Structure B on the tested input families and sizes.
- The pattern with the largest measured count is the strongest **among the candidates tested**; finite experiments do not prove a universal worst case.
- `equal-reverse-arrival` tests tie-breaking and should be interpreted separately from the distinct-key lower-bound inputs.
- The benchmark reports comparator/key-comparison counts. It does not measure wall-clock runtime, memory use, hash-table probes, or general machine-operation counts.
- The benchmark workload is static build-then-extract. It does not model arrivals, updates, deletions, or aging during extraction.
- Re-run the experiments after changes to either heap implementation, the comparator, the generator, or the benchmark.

For the exact recorded measurements and detailed discussion, see [`Report.md`](Report.md) and the generated CSV files.


