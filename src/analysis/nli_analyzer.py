"""
NLI Comparison Analysis

This module provides NL comparison analysis without LLM calls.
Can be run multiple times after data generation is complete.

Categories (based on bidirectional MNLI):
  - CONTRADICTION: C_max ≥ 0.6 (genuine semantic conflict)
  - EQUIVALENT: E_min ≥ 0.7 and C_max < 0.2 (strong mutual entailment)
  - STRENGTHENED: reconstruction adds constraints (E1 high, E2 low)
  - WEAKENED: reconstruction drops constraints (E2 high, E1 low)
  - RELATED: some mutual entailment
  - UNRELATED: no clear relationship
"""

from pathlib import Path
from datetime import datetime
from .nl_comparator import compare_rules

# Categories in display order (worst to best for review priority)
CATEGORIES = ['CONTRADICTION', 'UNRELATED', 'WEAKENED', 'STRENGTHENED', 'RELATED', 'EQUIVALENT']


def analyze_nli_folder(folder: Path):
    """
    Analyze NLI comparison on any folder with standard structure.
    
    Expects folder to contain rule subdirectories, each with:
        original_nl.txt
        reconstructed_nl.txt
    
    Works on: repair_full dirs, repair_random dirs, etc.
    Writes results to: <folder>/nli_analysis.log
    
    Args:
        folder: Path to any folder containing rule subdirs with the standard files
    """
    print(f"\nAnalyzing NLI Comparison: {folder}")
    print("="*80)
    
    # Find all rule subdirectories
    rule_dirs = [d for d in sorted(folder.iterdir()) if d.is_dir()]
    
    if not rule_dirs:
        print("  No subdirectories found. Nothing to analyze.")
        return
    
    # Collect comparisons
    comparisons = []
    for idx, rule_dir in enumerate(rule_dirs, 1):
        rule_name = rule_dir.name
        
        # Skip non-rule directories
        if rule_name in ('config',):
            continue
        
        print(f"  [{idx}/{len(rule_dirs)}] {rule_name}...", end=" ")
        
        original_file = rule_dir / 'original_nl.txt'
        reconstructed_file = rule_dir / 'reconstructed_nl.txt'
        
        if not original_file.exists():
            print("SKIPPED (no original_nl.txt)")
            continue
        
        if not reconstructed_file.exists():
            print("SKIPPED (no reconstructed_nl.txt)")
            continue
        
        with open(original_file, 'r') as f:
            original_nl = f.read().strip()
        
        with open(reconstructed_file, 'r') as f:
            reconstructed_nl = f.read().strip()
        
        comparisons.append({
            'rule_name': rule_name,
            'original': original_nl,
            'reconstructed': reconstructed_nl
        })
        
        print("OK")
    
    if not comparisons:
        print("\nNo rules to compare. Skipping NLI analysis.")
        return
    
    # Run NLI comparison
    print(f"\nRunning NLI model on {len(comparisons)} rule pairs...")
    
    results = []
    for comparison in comparisons:
        result = compare_rules(
            comparison['original'],
            comparison['reconstructed'],
            comparison['rule_name']
        )
        results.append(result)
    
    # Write results
    log_path = folder / 'nli_analysis.log'
    _write_nli_log(log_path, results)
    
    # Print summary
    counts = {cat: 0 for cat in CATEGORIES}
    counts['ERROR'] = 0
    for result in results:
        cat = result.get('equivalence', 'ERROR')
        if cat in counts:
            counts[cat] += 1
        else:
            counts['ERROR'] += 1
    
    print(f"\nNLI Comparison Summary:")
    print(f"  CONTRADICTION: {counts['CONTRADICTION']}")
    print(f"  UNRELATED:     {counts['UNRELATED']}")
    print(f"  WEAKENED:      {counts['WEAKENED']}")
    print(f"  STRENGTHENED:  {counts['STRENGTHENED']}")
    print(f"  RELATED:       {counts['RELATED']}")
    print(f"  EQUIVALENT:    {counts['EQUIVALENT']}")
    print(f"  ERROR:         {counts['ERROR']}")
    print(f"  Total:         {len(results)}")
    print(f"\nResults written to: {log_path}")


def analyze_nli(run_dir: Path):
    """
    Analyze NLI comparison between original and reconstructed NL.
    
    Writes results to: nli_comparison.log
    
    Args:
        run_dir: Path to the run directory
    """
    print("\nAnalyzing NLI Comparison (Original vs Reconstructed NL)")
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
    
    # Collect all comparisons
    comparisons = []
    for idx, rule_dir in enumerate(rule_dirs, 1):
        rule_name = rule_dir.name
        print(f"  [{idx}/{len(rule_dirs)}] {rule_name}...", end=" ")
        
        # Check for iteration_0. Missing iteration_0 with a schema_issue_*
        # file means the rule was deliberately skipped during baseline
        # (schema-insufficient flag from the LLM); skip gracefully.
        iter0_dir = rule_dir / 'iteration_0'
        if not iter0_dir.exists():
            if (rule_dir / 'schema_issue_phase1.txt').exists() or \
               (rule_dir / 'schema_issue_phase3.txt').exists():
                print("SKIPPED (schema-insufficient flag)")
                continue
            raise FileNotFoundError(
                f"iteration_0 directory not found in {rule_dir}.\n"
                f"This run directory appears to be from an old format.\n"
                f"Please re-run the roundtrip to generate iteration_0 baseline files."
            )
        
        original_file = rule_dir / 'original_nl.txt'  # Always in root
        reconstructed_file = iter0_dir / 'reconstructed_nl.txt'
        
        if not original_file.exists():
            print("SKIPPED (no original NL)")
            continue
        
        if not reconstructed_file.exists():
            print("SKIPPED (no reconstructed NL)")
            continue
        
        with open(original_file, 'r') as f:
            original_nl = f.read().strip()
        
        with open(reconstructed_file, 'r') as f:
            reconstructed_nl = f.read().strip()
        
        comparisons.append({
            'rule_name': rule_name,
            'original': original_nl,
            'reconstructed': reconstructed_nl
        })
        
        print("OK")
    
    if not comparisons:
        print("\nNo rules to compare. Skipping NLI analysis.")
        return
    
    # Run NLI comparison
    print(f"\nRunning NLI model on {len(comparisons)} rule pairs...")
    
    results = []
    for comparison in comparisons:
        result = compare_rules(
            comparison['original'],
            comparison['reconstructed'],
            comparison['rule_name']
        )
        results.append(result)
    
    # Write results
    log_path = run_dir / 'nli_comparison.log'
    _write_nli_log(log_path, results)
    
    # Print summary
    counts = {cat: 0 for cat in CATEGORIES}
    counts['ERROR'] = 0
    for result in results:
        cat = result.get('equivalence', 'ERROR')
        if cat in counts:
            counts[cat] += 1
        else:
            counts['ERROR'] += 1
    
    print(f"\nNLI Comparison Summary:")
    print(f"  CONTRADICTION: {counts['CONTRADICTION']} (C_max ≥ 0.6 - genuine semantic conflict)")
    print(f"  UNRELATED:     {counts['UNRELATED']} (no mutual entailment)")
    print(f"  WEAKENED:      {counts['WEAKENED']} (reconstruction drops constraints)")
    print(f"  STRENGTHENED:  {counts['STRENGTHENED']} (reconstruction adds constraints)")
    print(f"  RELATED:       {counts['RELATED']} (some mutual entailment)")
    print(f"  EQUIVALENT:    {counts['EQUIVALENT']} (strong mutual entailment)")
    print(f"  ERROR:         {counts['ERROR']}")
    print(f"  Total:         {len(results)}")
    print(f"\nResults written to: {log_path}")


def _write_nli_log(log_path: Path, results: list):
    """Write NLI comparison results to log file."""
    # Clear file first (don't append)
    with open(log_path, 'w') as f:
        f.write("="*80 + "\n")
        f.write(f"NLI COMPARISON ANALYSIS\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n")
        f.write("Comparing: original_nl.txt vs reconstructed_nl.txt (iteration_0)\n")
        f.write("Model: facebook/bart-large-mnli (bidirectional)\n\n")
        f.write("Key signals:\n")
        f.write("  E_min = min(E1, E2): Both directions must entail for equivalence\n")
        f.write("  C_max = max(C1, C2): Any contradiction is concerning\n")
        f.write("  E1 = P(original entails reconstructed)\n")
        f.write("  E2 = P(reconstructed entails original)\n\n")
        f.write("Categories:\n")
        f.write("  CONTRADICTION: C_max ≥ 0.6 (genuine semantic conflict)\n")
        f.write("  EQUIVALENT:    E_min ≥ 0.7 and C_max < 0.2\n")
        f.write("  STRENGTHENED:  E1 ≥ 0.6, E2 < 0.4 (recon adds constraints)\n")
        f.write("  WEAKENED:      E2 ≥ 0.6, E1 < 0.4 (recon drops constraints)\n")
        f.write("  RELATED:       E_min ≥ 0.3, C_max < 0.3\n")
        f.write("  UNRELATED:     otherwise\n\n")
        
        # Group by category (in priority order for review)
        for category in CATEGORIES + ['ERROR']:
            filtered = [r for r in results if r.get('equivalence') == category]
            if filtered:
                f.write(f"\n{'='*80}\n")
                f.write(f"{category} ({len(filtered)} rules)\n")
                f.write("-"*80 + "\n")
                for result in filtered:
                    f.write(f"\nRule: {result['rule_name']}\n")
                    f.write(f"  E1={result.get('forward_entailment', 0):.3f} (orig→recon), ")
                    f.write(f"E2={result.get('backward_entailment', 0):.3f} (recon→orig)\n")
                    f.write(f"  E_min={result.get('E_min', 0):.3f}, C_max={result.get('C_max', 0):.3f}, ")
                    f.write(f"Score={result.get('score', 0):.3f}\n")
                    f.write(f"  Original:      {result.get('original_nl', '')}\n")
                    f.write(f"  Reconstructed: {result.get('reconstructed_nl', '')}\n")
                    f.write(f"  Rationale: {result.get('rationale', 'N/A')}\n")
        
        # Summary
        counts = {cat: 0 for cat in CATEGORIES}
        counts['ERROR'] = 0
        scores = []
        for result in results:
            cat = result.get('equivalence', 'ERROR')
            if cat in counts:
                counts[cat] += 1
            else:
                counts['ERROR'] += 1
            scores.append(result.get('score', 0))
        
        f.write("\n" + "="*80 + "\n")
        f.write("SUMMARY:\n")
        f.write(f"  CONTRADICTION: {counts['CONTRADICTION']} (C_max ≥ 0.6 - semantic conflict)\n")
        f.write(f"  UNRELATED:     {counts['UNRELATED']} (no mutual entailment)\n")
        f.write(f"  WEAKENED:      {counts['WEAKENED']} (recon drops constraints)\n")
        f.write(f"  STRENGTHENED:  {counts['STRENGTHENED']} (recon adds constraints)\n")
        f.write(f"  RELATED:       {counts['RELATED']} (some mutual entailment)\n")
        f.write(f"  EQUIVALENT:    {counts['EQUIVALENT']} (strong mutual entailment)\n")
        f.write(f"  ERROR:         {counts['ERROR']}\n")
        f.write(f"  Total:         {len(results)}\n")
        if scores:
            f.write(f"\n  Score (E_min - C_max) statistics:\n")
            f.write(f"    Min:    {min(scores):.3f}\n")
            f.write(f"    Max:    {max(scores):.3f}\n")
            f.write(f"    Median: {sorted(scores)[len(scores)//2]:.3f}\n")
            f.write(f"    Mean:   {sum(scores)/len(scores):.3f}\n")
        f.write("="*80 + "\n")

