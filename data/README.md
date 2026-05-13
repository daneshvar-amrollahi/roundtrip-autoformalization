# Paper data

This directory contains the four primary experimental runs used in the paper
and the cross-model diagnosis runs. Together they cover every cell of the
main results tables.

## Run directories

| Directory | Domain | Pipeline / Repair model | $N$ |
|-----------|--------|--------------------------|---:|
| `traffic_claude/`   | Texas Transportation Code      | Claude Opus 4.6 | 150 |
| `traffic_gpt/`      | Texas Transportation Code      | GPT-5.2         | 150 |
| `wildlife_claude/`  | Texas Parks and Wildlife Code  | Claude Opus 4.6 |  77 |
| `wildlife_gpt/`     | Texas Parks and Wildlife Code  | GPT-5.2         |  77 |

Sampling: temperature 0.3, top_p 0.85 for every LLM call.

## Layout of each run directory

```
<run>/
|-- config/                      # snapshot of prompts and schema used
|-- pipeline.log                 # T_1 / T_2 / T_3 generation log
|-- smt_pre_repair.log           # baseline Z3 verdicts (None column of Table 1)
|-- nli_comparison.log           # baseline NLI categories
|-- repair_stats_full.json       # aggregates for Full ablation
|-- repair_stats_random.json     # aggregates for Random Stage ablation
|-- repair_stats_regenerate.json # aggregates for Regenerate ablation
|-- repair_stats_full_xclaude.json   # only in traffic_gpt/ and wildlife_gpt/
|-- r001/                        # one directory per rule (or wl001/ for wildlife)
|   |-- original_nl.txt          # input statutory rule x
|   |-- encoding_phase1.smt2     # T_1(x)
|   |-- reconstructed_nl.txt     # T_2(T_1(x))
|   |-- encoding_phase3.smt2     # T_3(T_2(T_1(x)))
|   |-- eq_check_phase1_vs_phase3.smt2
|   `-- iteration_0/             # baseline Z3 check
|       `-- z3_result.txt
|-- repair_full/                 # per-rule post-repair artifacts for the Full ablation
|   |-- r001/
|   |   |-- encoding_phase1.smt2    # final post-repair
|   |   |-- encoding_phase3.smt2    # final post-repair
|   |   |-- reconstructed_nl.txt    # final post-repair
|   |   |-- repair_summary.txt      # final verdict + per-iteration history
|   |   |-- iteration_1/
|   |   |   |-- diagnosis.txt       # contains "First Failed Arrow: <1|2|3>"
|   |   |   `-- z3_result.txt
|   |   |-- iteration_2/ ...
|   |   `-- iteration_3/ ...
|   |-- smt_analysis.log         # SAT/UNSAT per rule under this ablation
|   `-- nli_analysis.log         # NLI category per rule on the final post-repair NL pair
|-- repair_random/               # same layout, Random Stage ablation
|-- repair_regenerate/           # same layout, Regenerate ablation
`-- repair_full_xclaude/         # only in traffic_gpt/ and wildlife_gpt/
                                 # Full ablation with Claude (Opus 4.6) as diagnoser, GPT-5.2 as pipeline + repair
```

## Reproducing the paper tables

All commands below are offline (no LLM calls). Run them from the repository
root after `pip install -r requirements.txt`. Each command prints a summary
to stdout and appends a section to a log file inside the run directory.

### Table 1, None column (baseline UNSAT count)

```bash
python main.py --analyze-smt-pre data/traffic_claude
python main.py --analyze-smt-pre data/traffic_gpt
python main.py --analyze-smt-pre data/wildlife_claude
python main.py --analyze-smt-pre data/wildlife_gpt
```

Each command prints lines like `UNSAT (equivalent): N`. The value of `N` is
the corresponding entry in the None column. The `wildlife_gpt` run also
reports `SKIPPED: 1` (rule `wl015`), which the paper excludes from
post-repair counts per the Wildlife footnote.

### Table 1, Random / Regenerate / Full columns (post-repair UNSAT count)

```bash
# Random
python main.py --analyze-smt data/traffic_claude/repair_random
python main.py --analyze-smt data/traffic_gpt/repair_random
python main.py --analyze-smt data/wildlife_claude/repair_random
python main.py --analyze-smt data/wildlife_gpt/repair_random

# Regenerate
python main.py --analyze-smt data/traffic_claude/repair_regenerate
python main.py --analyze-smt data/traffic_gpt/repair_regenerate
python main.py --analyze-smt data/wildlife_claude/repair_regenerate
python main.py --analyze-smt data/wildlife_gpt/repair_regenerate

# Full
python main.py --analyze-smt data/traffic_claude/repair_full
python main.py --analyze-smt data/traffic_gpt/repair_full
python main.py --analyze-smt data/wildlife_claude/repair_full
python main.py --analyze-smt data/wildlife_gpt/repair_full
```

Each command prints lines like `UNSAT (equivalent): N`.

### Table 1, cross-model row (GPT pipeline with Claude diagnoser)

```bash
python main.py --analyze-smt data/traffic_gpt/repair_full_xclaude
python main.py --analyze-smt data/wildlife_gpt/repair_full_xclaude
```

### Table 1, LLM calls per repair

The `llm_calls_per_unsat` field of each `repair_stats_<method>.json`:

```bash
for cell in traffic_claude traffic_gpt wildlife_claude wildlife_gpt; do
  for method in random regenerate full; do
    f="data/$cell/repair_stats_${method}.json"
    echo "$cell / $method:"
    python3 -c "import json; print('  llm_calls_per_unsat =', json.load(open('$f'))['llm_calls_per_unsat'])"
  done
done

# Cross-model
python3 -c "import json; print('traffic_gpt  / Full+Claude-dx:  llm_calls_per_unsat =', json.load(open('data/traffic_gpt/repair_stats_full_xclaude.json'))['llm_calls_per_unsat'])"
python3 -c "import json; print('wildlife_gpt / Full+Claude-dx:  llm_calls_per_unsat =', json.load(open('data/wildlife_gpt/repair_stats_full_xclaude.json'))['llm_calls_per_unsat'])"
```

### Table 2, NLI drift split by SMT verdict

The per-rule NLI category for every cell × method is already in the
`nli_analysis.log` file under each `repair_*` directory. The per-rule SMT
verdict is in the corresponding `smt_analysis.log`. To regenerate either
from raw artifacts:

```bash
# SMT verdicts (no extra deps beyond what is already in the venv)
python main.py --analyze-smt data/<cell>/<repair_dir>

# NLI categories (requires transformers + torch; CPU is fine)
python main.py --analyze-nli data/<cell>/<repair_dir>
```

To compute the drift split per cell × method, count rules per
(SMT verdict, NLI category) pair using both logs. Drift = the rules
labelled `UNRELATED` or `CONTRADICTION` in `nli_analysis.log`. The UNSAT and
SAT pools come from the rules under those headers in `smt_analysis.log`.

The pooled row of Table 2 pools across all four methods
(Random + Regenerate + Full + Full+Claude-diagnoser). The 2.03 ratio
mentioned in the prose pools across the four Full configurations only.

### Stage diagnosis distribution (Appendix table)

For each cell and method, count the values of `First Failed Arrow: <1|2|3>`
across every `repair_<method>/<rule>/iteration_<k>/diagnosis.txt`:

```bash
for cell in traffic_claude traffic_gpt wildlife_claude wildlife_gpt; do
  for method in random regenerate full; do
    echo "--- $cell / $method ---"
    grep -h "First Failed Arrow" data/$cell/repair_$method/*/iteration_*/diagnosis.txt | sort | uniq -c
  done
done
```

### Residual rules (Section 7.5)

A rule is residual in a cell if `repair_summary.txt` reports
`Final Result: NOT EQUIVALENT (SAT)` under all three methods (Random,
Regenerate, Full) for that cell:

```bash
for cell in traffic_claude traffic_gpt wildlife_claude wildlife_gpt; do
  for r in data/$cell/repair_full/*/; do
    rule=$(basename "$r")
    [ -d "$r" ] && [ "$rule" != "config" ] || continue
    all_sat=1
    for m in random regenerate full; do
      f="data/$cell/repair_$m/$rule/repair_summary.txt"
      [ -f "$f" ] || { all_sat=0; break; }
      grep -q "Final Result: NOT EQUIVALENT (SAT)" "$f" || { all_sat=0; break; }
    done
    [ "$all_sat" = "1" ] && echo "$cell $rule"
  done
done
```

The 28 residual rules referenced in the paper are the union over all four
cells of these triple-failure rules.

### Table 1 (final UNSAT counts and LLM-calls per repair)

```bash
# None column (baseline UNSAT count per cell)
python main.py --analyze-smt-pre data/traffic_claude
python main.py --analyze-smt-pre data/traffic_gpt
python main.py --analyze-smt-pre data/wildlife_claude
python main.py --analyze-smt-pre data/wildlife_gpt

# Random / Regenerate / Full / cross-model columns
for cell in traffic_claude traffic_gpt wildlife_claude wildlife_gpt; do
  for abl in repair_random repair_regenerate repair_full; do
    python main.py --analyze-smt data/$cell/$abl
  done
done
python main.py --analyze-smt data/traffic_gpt/repair_full_xclaude
python main.py --analyze-smt data/wildlife_gpt/repair_full_xclaude
```

LLM-calls per repair for each cell are reported directly in
`repair_stats_<ablation>.json` as the `llm_calls_per_unsat` field.

Note: `wildlife_gpt` has one baseline-skipped rule (`wl015`). The paper
excludes this rule from post-repair UNSAT counts, which is why the Wildlife/GPT
row of Table 1 reads $N=77$ with a footnote.

### Table 2 (NLI drift split by SMT verdict)

The post-repair NLI category per rule is already computed in each
`repair_<abl>/nli_analysis.log`. Drift = rules labelled `UNRELATED` or
`CONTRADICTION`. The SAT and UNSAT pools come from the corresponding
`smt_analysis.log` in the same directory.

To regenerate `nli_analysis.log` from scratch (optional, requires the
`transformers` and `torch` packages, no LLM API needed):

```bash
for cell in traffic_claude traffic_gpt wildlife_claude wildlife_gpt; do
  for abl in repair_random repair_regenerate repair_full; do
    python main.py --analyze-nli data/$cell/$abl
  done
done
python main.py --analyze-nli data/traffic_gpt/repair_full_xclaude
python main.py --analyze-nli data/wildlife_gpt/repair_full_xclaude
```

The pooled row of Table 2 pools across all four methods
(Random + Regenerate + Full + Full+Claude-diagnoser). The 2.03 ratio reported
in the prose pools across the four Full configurations only.

### Stage diagnosis distribution (Table 7 / Appendix)

For each cell and method, count the values of `First Failed Arrow: <1|2|3>`
in `repair_<abl>/<rule>/iteration_<k>/diagnosis.txt` across all SAT rules.

### Residual rules (Section 7.5)

A rule is residual in a cell if `repair_summary.txt` reports
`Final Result: NOT EQUIVALENT (SAT)` under all three methods (Random,
Regenerate, Full) for that cell. The 28 residual rules in the paper are the
union across all four cells.

## Sizes

| Directory | Size |
|-----------|-----:|
| `traffic_claude/` | 101 MB |
| `traffic_gpt/`    | 103 MB |
| `wildlife_claude/`|  37 MB |
| `wildlife_gpt/`   |  44 MB |
| **Total**         | **285 MB** |
