"""
Experiment A: Non-sequential diagnosis ablation.

Re-runs the diagnosis function on the existing GPT SAT pools (Traffic + Wildlife)
using a non-sequential prompt instead of the sequential one used in the main runs.
Compares the resulting T1/T2/T3 distribution against the original sequential-prompt
distribution recorded in each rule's iteration_1/diagnosis.txt.

Hypothesis to test: whether the T_1 concentration observed under the GPT pipeline
is induced by the sequential checking protocol. With a non-sequential prompt, the
T_1 rate should drop substantially if the protocol is the cause; otherwise the
bias is intrinsic to the model.

Usage:
  OPENAI_API_KEY=... python run_experiment_a.py \\
      --traffic-run-dir  output/run_YYYYMMDD_HHMMSS_traffic \\
      --wildlife-run-dir output/run_YYYYMMDD_HHMMSS_wildlife

Pass --traffic-run-dir or --wildlife-run-dir alone to run only one domain.
"""

from __future__ import annotations
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from src.llm_client import LLMClient


def build_cells(traffic_run_dir: Path | None, wildlife_run_dir: Path | None) -> list[dict]:
    cells = []
    if traffic_run_dir is not None:
        cells.append({
            "name": "Traffic / GPT",
            "domain": "traffic",
            "run_dir": traffic_run_dir,
            "rule_glob": "r???",
        })
    if wildlife_run_dir is not None:
        cells.append({
            "name": "Wildlife / GPT",
            "domain": "wildlife",
            "run_dir": wildlife_run_dir,
            "rule_glob": "wl???",
        })
    return cells


def load_text(p: Path) -> str:
    return p.read_text().strip()


def is_sat_rule(rule_dir: Path) -> bool:
    z3 = rule_dir / "iteration_0" / "z3_result.txt"
    if not z3.exists():
        return False
    return "Result: SAT" in z3.read_text()


def parse_baseline_arrow(rule_dir: Path) -> int | None:
    """Extract the OLD (sequential-prompt) arrow choice from iteration_1/diagnosis.txt."""
    diag = rule_dir.parent.parent / "repair_full" / rule_dir.name / "iteration_1" / "diagnosis.txt"
    if not diag.exists():
        return None
    text = diag.read_text()
    m = re.search(r"First Failed Arrow:\s*(\d)", text)
    return int(m.group(1)) if m else None


def parse_new_arrow(response: str) -> int | None:
    m = re.search(r"FIRST_FAILED_ARROW:\s*(\d)", response)
    if m:
        return int(m.group(1))
    # fallback: any 1/2/3 right after the field name
    m = re.search(r"FIRST[_\s]FAILED[_\s]ARROW[^0-9]*(\d)", response)
    return int(m.group(1)) if m else None


def diagnose_with_nonseq(client: LLMClient, prompt_template: str, schema: str,
                          original_nl: str, phase1_smt: str,
                          reconstructed_nl: str, phase3_smt: str) -> tuple[str, int | None]:
    prompt = prompt_template.format(
        original_nl=original_nl,
        phase1_smt=phase1_smt,
        reconstructed_nl=reconstructed_nl,
        phase3_smt=phase3_smt,
    )
    full_prompt = prompt + "\n\nDOMAIN SCHEMA (for context):\n" + schema
    response = client.generate_with_prompt(full_prompt, temperature=0.3)
    return response, parse_new_arrow(response)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--traffic-run-dir", type=Path, default=None,
                        help="Path to a baseline GPT run directory for the traffic domain "
                             "(contains rXXX/iteration_0/ and repair_full/rXXX/iteration_1/).")
    parser.add_argument("--wildlife-run-dir", type=Path, default=None,
                        help="Path to a baseline GPT run directory for the wildlife domain.")
    parser.add_argument("--model", default="gpt-5.2",
                        help="OpenAI model to use for the non-sequential diagnosis (default: gpt-5.2).")
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "experiment_a_results",
                        help="Directory to write per-cell JSON summaries.")
    args = parser.parse_args()

    if args.traffic_run_dir is None and args.wildlife_run_dir is None:
        parser.error("Pass at least one of --traffic-run-dir / --wildlife-run-dir.")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set in env", file=sys.stderr)
        sys.exit(1)

    client = LLMClient(api_key=api_key, model=args.model, temperature=0.3,
                       top_p=0.85, provider="openai")

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    cells = build_cells(args.traffic_run_dir, args.wildlife_run_dir)
    summary = {}

    for cell in cells:
        print(f"\n=== {cell['name']} ===")
        cell_run_dir = cell["run_dir"]
        domain = cell["domain"]

        prompt_path = REPO_ROOT / "config" / "domains" / domain / "prompts" / "diagnosis_prompt_nonseq.txt"
        prompt_template = prompt_path.read_text()

        schema_path = REPO_ROOT / "config" / "domains" / domain / "schema.smt2"
        schema = schema_path.read_text()

        rule_dirs = sorted([d for d in cell_run_dir.iterdir() if d.is_dir() and d.name.startswith(("r", "wl"))
                            and not d.name.startswith("repair_") and not d.name == "config"])
        sat_dirs = [d for d in rule_dirs if is_sat_rule(d)]
        print(f"Found {len(sat_dirs)} SAT rules")

        per_rule = []
        for i, rule_dir in enumerate(sat_dirs, 1):
            rule = rule_dir.name
            try:
                x = load_text(rule_dir / "original_nl.txt")
                y_orig = load_text(rule_dir / "encoding_phase1.smt2")
                xp = load_text(rule_dir / "reconstructed_nl.txt")
                y_rt = load_text(rule_dir / "encoding_phase3.smt2")
            except FileNotFoundError as e:
                print(f"  [{i}/{len(sat_dirs)}] {rule}: missing artifact: {e}")
                continue

            baseline_arrow = parse_baseline_arrow(rule_dir)

            try:
                response, new_arrow = diagnose_with_nonseq(
                    client, prompt_template, schema, x, y_orig, xp, y_rt
                )
            except Exception as e:
                print(f"  [{i}/{len(sat_dirs)}] {rule}: API error: {e}")
                continue

            print(f"  [{i}/{len(sat_dirs)}] {rule}: baseline T{baseline_arrow} -> new T{new_arrow}")

            per_rule.append({
                "rule": rule,
                "baseline_arrow": baseline_arrow,
                "nonseq_arrow": new_arrow,
                "nonseq_response": response,
            })
            time.sleep(1)

        # Aggregate
        from collections import Counter
        baseline_dist = Counter(r["baseline_arrow"] for r in per_rule if r["baseline_arrow"])
        nonseq_dist = Counter(r["nonseq_arrow"] for r in per_rule if r["nonseq_arrow"])
        n = len([r for r in per_rule if r["nonseq_arrow"]])

        cell_summary = {
            "n_sat_rules": len(per_rule),
            "n_with_nonseq": n,
            "baseline_dist": dict(baseline_dist),
            "nonseq_dist": dict(nonseq_dist),
            "baseline_pct": {k: 100.0 * v / sum(baseline_dist.values())
                              for k, v in baseline_dist.items()} if baseline_dist else {},
            "nonseq_pct": {k: 100.0 * v / n for k, v in nonseq_dist.items()} if n else {},
        }
        summary[cell["name"]] = cell_summary
        print(f"  Baseline distribution: {cell_summary['baseline_pct']}")
        print(f"  Non-seq distribution:  {cell_summary['nonseq_pct']}")

        # Save per-cell details
        cell_out = out_dir / f"{domain}_gpt.json"
        with open(cell_out, "w") as f:
            json.dump({"cell": cell["name"], "per_rule": per_rule, "summary": cell_summary},
                       f, indent=2)
        print(f"  Saved per-rule details to {cell_out}")

    # Save aggregate summary
    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nFinal summary saved to {out_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
