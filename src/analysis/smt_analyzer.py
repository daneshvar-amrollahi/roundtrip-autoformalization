"""
SMT Equivalence Analysis - Pre and Post Repair

This module provides analysis of SMT equivalence without LLM calls.
Can be run multiple times after data generation is complete.
"""

import subprocess
from pathlib import Path
from typing import Dict, Tuple
from datetime import datetime


def analyze_smt_pre_repair(run_dir: Path, schema_content: str):
    """
    Analyze SMT equivalence BEFORE repair (Phase 1 vs Phase 3).
    
    Writes results to: smt_pre_repair.log
    
    Args:
        run_dir: Path to the run directory
        schema_content: SMT schema content
    """
    print("\nAnalyzing SMT Equivalence (Pre-Repair: Phase 1 vs Phase 3)")
    print("="*80)

    # Find all rule directories: any dir containing original_nl.txt (excludes
    # 'config' and per-ablation 'repair_*' subdirs).
    rule_dirs = [
        d for d in sorted(run_dir.iterdir())
        if d.is_dir()
        and not d.name.startswith('repair_')
        and d.name != 'config'
        and (d / 'original_nl.txt').exists()
    ]
    
    results = {}
    counts = {'UNSAT': 0, 'SAT': 0, 'UNKNOWN': 0, 'ERROR': 0, 'SKIPPED': 0}
    
    for idx, rule_dir in enumerate(rule_dirs, 1):
        rule_name = rule_dir.name
        print(f"  [{idx}/{len(rule_dirs)}] {rule_name}...", end=" ")
        
        result = _check_phase1_vs_phase3(rule_dir, schema_content)
        results[rule_name] = result
        counts[result] += 1
        
        print(result)
    
    # Write results
    _write_smt_pre_repair_log(run_dir, results, counts)
    
    # Print summary
    print(f"\nSMT Equivalence (Pre-Repair) Summary:")
    print(f"  UNSAT (equivalent): {counts['UNSAT']}")
    print(f"  SAT (different):    {counts['SAT']}")
    print(f"  UNKNOWN:            {counts['UNKNOWN']}")
    print(f"  ERROR:              {counts['ERROR']}")
    print(f"  SKIPPED:            {counts['SKIPPED']}")
    print(f"\nResults written to: {run_dir / 'smt_pre_repair.log'}")


def analyze_smt_folder(folder: Path, schema_content: str):
    """
    Analyze SMT equivalence on any folder with standard structure.
    
    Expects folder to contain rule subdirectories, each with:
        encoding_phase1.smt2
        encoding_phase3.smt2
    
    Works on: iteration_0 dirs, repair_full dirs, repair_random dirs, etc.
    Writes results to: <folder>/smt_analysis.log
    
    Args:
        folder: Path to any folder containing rule subdirs with the standard files
        schema_content: SMT schema content
    """
    print(f"\nAnalyzing SMT Equivalence: {folder}")
    print("="*80)
    
    # Find all rule subdirectories
    rule_dirs = [d for d in sorted(folder.iterdir()) if d.is_dir()]
    
    if not rule_dirs:
        print("  No subdirectories found. Checking if folder itself has the files...")
        # Maybe folder IS a rule dir — not applicable here
        print("  Nothing to analyze.")
        return
    
    results = {}
    counts = {'UNSAT': 0, 'SAT': 0, 'UNKNOWN': 0, 'ERROR': 0, 'SKIPPED': 0}
    
    for idx, rule_dir in enumerate(rule_dirs, 1):
        rule_name = rule_dir.name
        
        # Skip non-rule directories
        if rule_name in ('config',):
            continue
        
        print(f"  [{idx}/{len(rule_dirs)}] {rule_name}...", end=" ")
        
        # Look for encoding files directly in the rule_dir
        phase1_file = rule_dir / 'encoding_phase1.smt2'
        phase3_file = rule_dir / 'encoding_phase3.smt2'
        
        if not phase1_file.exists() or not phase3_file.exists():
            print("SKIPPED (missing files)")
            results[rule_name] = 'SKIPPED'
            counts['SKIPPED'] += 1
            continue
        
        with open(phase1_file, 'r') as f:
            phase1_smt = f.read().strip()
        with open(phase3_file, 'r') as f:
            phase3_smt = f.read().strip()
        
        # Create benchmark
        benchmark_content = _create_equivalence_benchmark(phase1_smt, phase3_smt, schema_content)
        benchmark_path = rule_dir / "eq_check.smt2"
        
        with open(benchmark_path, 'w') as f:
            f.write(benchmark_content)
        
        result = _run_z3(benchmark_path)
        results[rule_name] = result
        counts[result] += 1
        print(result)
    
    # Write log
    log_path = folder / 'smt_analysis.log'
    with open(log_path, 'w') as f:
        f.write("="*80 + "\n")
        f.write(f"SMT EQUIVALENCE ANALYSIS\n")
        f.write(f"Folder: {folder}\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n")
        f.write("Comparing: encoding_phase1.smt2 vs encoding_phase3.smt2\n\n")
        
        for result_type in ['UNSAT', 'SAT', 'UNKNOWN', 'ERROR', 'SKIPPED']:
            rules = [rule for rule, res in sorted(results.items()) if res == result_type]
            if rules:
                f.write(f"{result_type} ({len(rules)} rules):\n")
                for rule in rules:
                    f.write(f"  - {rule}\n")
                f.write("\n")
        
        f.write("-"*80 + "\n")
        f.write("SUMMARY:\n")
        f.write(f"  UNSAT (equivalent): {counts['UNSAT']}\n")
        f.write(f"  SAT (different):    {counts['SAT']}\n")
        f.write(f"  UNKNOWN:            {counts['UNKNOWN']}\n")
        f.write(f"  ERROR:              {counts['ERROR']}\n")
        f.write(f"  SKIPPED:            {counts['SKIPPED']}\n")
        f.write(f"  Total:              {sum(counts.values())}\n")
        f.write("="*80 + "\n")
    
    # Print summary
    print(f"\nSMT Equivalence Summary:")
    print(f"  UNSAT (equivalent): {counts['UNSAT']}")
    print(f"  SAT (different):    {counts['SAT']}")
    print(f"  UNKNOWN:            {counts['UNKNOWN']}")
    print(f"  ERROR:              {counts['ERROR']}")
    print(f"  SKIPPED:            {counts['SKIPPED']}")
    print(f"\nResults written to: {log_path}")


def _check_phase1_vs_phase3(rule_dir: Path, schema_content: str) -> str:
    """Check equivalence between Phase 1 and Phase 3 (from iteration_0)."""
    iter0_dir = rule_dir / 'iteration_0'

    if not iter0_dir.exists():
        # Rule was skipped during baseline (schema-insufficient flag, or
        # incomplete roundtrip). roundtrip_processor explicitly does not
        # create iteration_0 in that case. Mark SKIPPED so the rule still
        # appears in the analysis log.
        if (rule_dir / 'schema_issue_phase1.txt').exists() or \
           (rule_dir / 'schema_issue_phase3.txt').exists():
            return 'SKIPPED'
        raise FileNotFoundError(
            f"iteration_0 directory not found in {rule_dir}.\n"
            f"This run directory appears to be from an old format.\n"
            f"Please re-run the roundtrip to generate iteration_0 baseline files."
        )
    
    phase1_file = iter0_dir / 'encoding_phase1.smt2'
    phase3_file = iter0_dir / 'encoding_phase3.smt2'
    
    if not phase1_file.exists() or not phase3_file.exists():
        return 'SKIPPED'
    
    # Read encodings
    with open(phase1_file, 'r') as f:
        phase1_smt = f.read().strip()
    with open(phase3_file, 'r') as f:
        phase3_smt = f.read().strip()
    
    # Create benchmark
    benchmark_content = _create_equivalence_benchmark(phase1_smt, phase3_smt, schema_content)
    benchmark_path = rule_dir / "eq_check_phase1_vs_phase3.smt2"
    
    with open(benchmark_path, 'w') as f:
        f.write(benchmark_content)
    
    # Run Z3
    return _run_z3(benchmark_path)


def _create_equivalence_benchmark(encoding1: str, encoding2: str, schema: str) -> str:
    """
    Create SMT benchmark to check equivalence.
    
    Strategy: Assert that the two encodings are NOT equivalent (XOR).
    - UNSAT = no counterexample exists → encodings ARE equivalent
    - SAT = found counterexample → encodings are different
    """
    benchmark = f"""; Equivalence check benchmark
; UNSAT = equivalent, SAT = different, UNKNOWN = couldn't determine

{schema}

; Assert that encoding1 and encoding2 are NOT equivalent
; If this is UNSAT, then they must be equivalent
(assert
  (not
    (=
      {encoding1}
      {encoding2}
    )
  )
)

(check-sat)
"""
    return benchmark


def _run_z3(benchmark_file: Path) -> str:
    """Run Z3 on a benchmark file."""
    try:
        result = subprocess.run(
            ['z3', str(benchmark_file)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout.strip().lower()
        
        if 'unsat' in output:
            return 'UNSAT'
        elif 'sat' in output and 'unsat' not in output:
            return 'SAT'
        elif 'unknown' in output:
            return 'UNKNOWN'
        else:
            return 'ERROR'
    
    except subprocess.TimeoutExpired:
        return 'TIMEOUT'
    except Exception as e:
        return 'ERROR'


def _write_smt_pre_repair_log(run_dir: Path, results: Dict[str, str], counts: Dict[str, int]):
    """Write SMT pre-repair analysis to log file."""
    log_path = run_dir / 'smt_pre_repair.log'
    
    with open(log_path, 'a') as f:
        f.write("\n\n")
        f.write("="*80 + "\n")
        f.write(f"SMT EQUIVALENCE ANALYSIS - PRE-REPAIR\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n")
        f.write("Comparing: encoding_phase1.smt2 vs encoding_phase3.smt2\n\n")
        
        # Group by result
        for result_type in ['UNSAT', 'SAT', 'UNKNOWN', 'ERROR', 'SKIPPED']:
            rules = [rule for rule, res in sorted(results.items()) if res == result_type]
            if rules:
                f.write(f"{result_type} ({len(rules)} rules):\n")
                for rule in rules:
                    f.write(f"  - {rule}\n")
                f.write("\n")
        
        # Summary
        f.write("-"*80 + "\n")
        f.write("SUMMARY:\n")
        f.write(f"  UNSAT (equivalent): {counts['UNSAT']}\n")
        f.write(f"  SAT (different):    {counts['SAT']}\n")
        f.write(f"  UNKNOWN:            {counts['UNKNOWN']}\n")
        f.write(f"  ERROR:              {counts['ERROR']}\n")
        f.write(f"  SKIPPED:            {counts['SKIPPED']}\n")
        f.write(f"  Total:              {sum(counts.values())}\n")
        f.write("="*80 + "\n")


