# Roundtrip Verification and Scoped Repair for Autoformalization

Code and data accompanying an anonymous ARR submission on roundtrip verification
of LLM autoformalization. The pipeline translates a natural-language rule into
SMT-LIB (`T_1`), reconstructs the SMT back to natural language (`T_2`),
re-formalizes that reconstruction (`T_3`), and checks formal equivalence of the
two SMT encodings with Z3. When the check fails, an iterative scoped-repair
procedure diagnoses which stage was responsible and rewrites only that stage.

Two statutory domains are included: 150 rules from the Texas Transportation
Code (`rules-traffic/`) and 77 rules from the Texas Parks and Wildlife Code
(`rules-wildlife/`).

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Z3 must be on PATH (see https://github.com/Z3Prover/z3 for install instructions;
# on macOS `brew install z3`, on Debian/Ubuntu `apt install z3`, or `pip install z3-solver`).
z3 --version

# API keys (used only by data-generation commands, not by analysis)
echo "your-openai-key"    > config/openai_api_key.txt
echo "your-anthropic-key" > config/anthropic_api_key.txt
```

The NLI analyzer uses `facebook/bart-large-mnli` via HuggingFace
`transformers`. The first run downloads the model.

## Quick start

A single rule, all four configurations, traffic domain:

```bash
RUN_DIR="output/run_$(date +%Y%m%d_%H%M%S)"

# Baseline: T_1 / T_2 / T_3 for every rule, no repair
python main.py --mode roundtrip --domain traffic

# Pre-repair analysis (no LLM calls)
python main.py --analyze-smt-pre $RUN_DIR
python main.py --analyze-nli-pre $RUN_DIR

# Repair ablations
python main.py --repair-sat $RUN_DIR --ablation random
python main.py --repair-sat $RUN_DIR --ablation regenerate
python main.py --repair-sat $RUN_DIR --ablation full

# Post-repair analysis for each ablation
for abl in random regenerate full; do
  python main.py --analyze-smt $RUN_DIR/repair_$abl
  python main.py --analyze-nli $RUN_DIR/repair_$abl
done
```

For the wildlife domain, pass `--domain wildlife` to `--mode roundtrip`. The
rules directory is selected automatically (`rules-traffic` or `rules-wildlife`).

## Pipeline

```
NL rule  --T1-->  SMT  --T2-->  NL  --T3-->  SMT
                  |                          |
                  +---- Z3 equivalence ------+
                            |
                  SAT       |       UNSAT
                  |                  done
                  v
        scoped repair (up to K=3 iterations)
            1. diagnose which stage to repair (T1, T2, or T3)
            2. rewrite that stage
            3. propagate downstream if needed
            4. re-check
```

Each rule's run produces `iteration_0/` with the baseline `encoding_phase1.smt2`,
`reconstructed_nl.txt`, `encoding_phase3.smt2`, and `z3_result.txt`. SAT rules
get `iteration_1/`, `iteration_2/`, `iteration_3/` during repair, plus a
`repair_summary.txt`.

## Ablations

| `--ablation`   | Diagnosis | Stage selection                    | Notes |
|----------------|-----------|------------------------------------|-------|
| `full`         | LLM       | from diagnosis                     | scoped repair with diagnosis-driven stage choice |
| `no_reasoning` | LLM       | from diagnosis                     | diagnosis reasoning stripped before being passed to the repair prompt |
| `random`       | none      | uniform over {T1, T2, T3}          | tests whether diagnosis matters |
| `regenerate`   | none      | re-runs T1, T2, T3 from original NL | tests whether scoped repair beats blind resampling |

## Data generation vs. analysis

LLM calls (cost money, run once):

| Flag | Effect |
|------|--------|
| `--mode roundtrip --domain {traffic,wildlife}` | runs T1, T2, T3 for every rule; writes `iteration_0/` |
| `--repair-sat $RUN_DIR --ablation $ABL`        | iterative repair on SAT rules under ablation `$ABL` |

Analysis (no LLM calls, free to re-run):

| Flag | Effect |
|------|--------|
| `--analyze-smt-pre  $RUN_DIR`      | Z3 equivalence on baseline `iteration_0/` |
| `--analyze-nli-pre  $RUN_DIR`      | NLI on baseline original vs. reconstructed NL |
| `--analyze-smt      $FOLDER`       | Z3 equivalence on any ablation folder |
| `--analyze-nli      $FOLDER`       | NLI on any ablation folder |

## Cross-model setup

To run the pipeline with one model and the diagnosis step with another
(e.g., the GPT-pipeline-with-Claude-diagnoser configuration), override the
provider for the repair invocation:

```bash
python main.py --repair-sat $RUN_DIR --ablation full --provider anthropic
```

Model and provider can also be set in `config/model_config.txt`.

## NLI categories

Bidirectional NLI on (original NL, reconstructed NL) using
`facebook/bart-large-mnli`. `E1 = P(orig entails recon)`, `E2 = P(recon entails orig)`,
`C_max = max(C1, C2)`, `E_min = min(E1, E2)`.

| Category      | Condition                                     |
|---------------|-----------------------------------------------|
| CONTRADICTION | `C_max >= 0.6`                                |
| EQUIVALENT    | `E_min >= 0.7` and `C_max < 0.2`              |
| STRENGTHENED  | `E1 >= 0.6`, `E2 < 0.4`, `C_max < 0.3`        |
| WEAKENED      | `E2 >= 0.6`, `E1 < 0.4`, `C_max < 0.3`        |
| RELATED       | `E_min >= 0.3`, `C_max < 0.3`                 |
| UNRELATED     | otherwise                                     |

The paper reports `EQUIVALENT` and `RELATED` together as "preserved" and the
rest as "drifted".

## Configuration

`config/model_config.txt`:

```
provider=openai            # openai or anthropic
model=gpt-5.2
temperature=0.3
top_p=0.85
request_delay=10
```

`config/domains/{traffic,wildlife}/schema.smt2`: SMT-LIB signature (sorts,
functions, enums) for the domain. The traffic schema is hand-curated. The
wildlife schema was bootstrapped from the traffic schema and refined
semi-automatically; see `config/domains/SCHEMA_DESIGN.md`.

`config/domains/{traffic,wildlife}/prompts/`:

| File | Used in |
|------|---------|
| `base_prompt.txt`               | shared system instructions for all stages |
| `roundtrip_promptNL2SMT.txt`    | `T_1` and `T_3` |
| `roundtrip_promptSMT2NL.txt`    | `T_2` |
| `diagnosis_prompt.txt`          | sequential diagnosis (used in main runs) |
| `diagnosis_prompt_nonseq.txt`   | non-sequential diagnosis (Experiment A) |
| `repair_arrow1_prompt.txt`      | repair operator for stage `T_1` |
| `repair_arrow2_prompt.txt`      | repair operator for stage `T_2` |
| `repair_arrow3_prompt.txt`      | repair operator for stage `T_3` |

## Project layout

```
.
|-- main.py                       # CLI entry point
|-- run_experiment_a.py           # non-sequential diagnosis ablation (Experiment A)
|-- src/
|   |-- llm_client.py             # OpenAI / Anthropic wrapper
|   |-- file_handler.py           # I/O
|   |-- roundtrip_processor.py    # roundtrip orchestration
|   |-- z3_checker.py             # SMT equivalence check
|   |-- modes/roundtrip.py        # roundtrip mode runner
|   |-- repair/                   # iterative scoped repair + ablations
|   `-- analysis/                 # SMT and NLI analyzers
|-- config/
|   |-- model_config.txt
|   `-- domains/
|       |-- SCHEMA_DESIGN.md
|       |-- traffic/   (schema.smt2 + prompts/)
|       `-- wildlife/  (schema.smt2 + prompts/)
|-- rules-traffic/                # 150 NL rules (r001.txt .. r150.txt)
|-- rules-wildlife/               # 77 NL rules (wl001.txt .. wl077.txt)
`-- data/                         # 4 paper runs (traffic_{claude,gpt}, wildlife_{claude,gpt})
```

## Reproducing paper numbers

The four primary runs used in the paper are included under `data/` as
`traffic_claude/`, `traffic_gpt/`, `wildlife_claude/`, `wildlife_gpt/`. The
cross-model diagnosis runs live inside `data/traffic_gpt/repair_full_xclaude/`
and `data/wildlife_gpt/repair_full_xclaude/`.

See `data/README.md` for the explicit list of commands that regenerate each
column of Tables 1 and 2 of the paper. All analyses are offline (no LLM
calls).

Each run writes:

* `repair_stats_{full,random,regenerate}.json` for the verified-equivalence
  rate, average iterations, and LLM-call counts reported in the main results
  table.
* `smt_analysis.log` and `nli_analysis.log` under each `repair_$ABL/` for
  per-rule equivalence and NLI category breakdowns. Cross-tabulating these
  two logs reproduces the drift split.

Experiment A (non-sequential diagnosis) is run with:

```bash
OPENAI_API_KEY=... python run_experiment_a.py
```

## Requirements

* Python 3.8+
* Z3 on `PATH`
* OpenAI and/or Anthropic API access for data generation
* `torch`, `transformers` for NLI (CPU is fine, GPU is faster)
* See `requirements.txt` for pinned packages

## License

To be released under an open-source license upon paper acceptance.
