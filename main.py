"""
Entry point for nl2smt - Natural Language to SMT translation.
"""

import sys
import json
import argparse
from pathlib import Path
from src.modes.roundtrip import run_roundtrip_mode


def main():
    """Main entry point."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="nl2smt: Natural Language to SMT formalization for autonomous vehicle traffic rules",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Workflow:
  1. Generate baseline:  python main.py --mode roundtrip --domain <traffic|wildlife>
  2. Analyze baseline:   python main.py --analyze-smt-pre <run_dir>
                         python main.py --analyze-nli-pre <run_dir>
  3. Apply repair:       python main.py --repair-sat <run_dir> --ablation <full|random|regenerate>
                         (run once per ablation; results land in <run_dir>/repair_<ablation>/)
  4. Analyze results:    python main.py --analyze-smt <run_dir>/repair_<ablation>
                         python main.py --analyze-nli <run_dir>/repair_<ablation>
                         (per-ablation; logs land alongside the rules)
  5. Headline numbers:   <run_dir>/repair_stats_<ablation>.json (auto-written in step 3)

All --analyze-* flags run offline (no LLM calls, free to repeat).
        """
    )
    parser.add_argument(
        '--mode',
        choices=['roundtrip'],
        default='roundtrip',
        help='Experiment mode to run (default: roundtrip)'
    )
    parser.add_argument(
        '--max-repair-attempts',
        type=int,
        default=5,
        help='Maximum attempts to repair malformed encodings (default: 5)'
    )
    parser.add_argument(
        '--repair-sat',
        type=str,
        metavar='RUN_DIR',
        help='Apply iterative oracle repair to SAT rules (up to 3 iterations with arrows 1/2/3)'
    )
    parser.add_argument(
        '--analyze-smt-pre',
        type=str,
        metavar='RUN_DIR',
        help='Analyze SMT equivalence (iteration_0 baseline) - no LLM calls'
    )
    parser.add_argument(
        '--analyze-nli-pre',
        type=str,
        metavar='RUN_DIR',
        help='Analyze NLI semantic similarity (iteration_0 baseline) - no LLM calls'
    )
    parser.add_argument(
        '--analyze-smt',
        type=str,
        metavar='FOLDER',
        help='Analyze SMT equivalence on any folder with standard structure (encoding_phase1.smt2, encoding_phase3.smt2) - no LLM calls'
    )
    parser.add_argument(
        '--analyze-nli',
        type=str,
        metavar='FOLDER',
        help='Analyze NLI semantic similarity on any folder with standard structure (original_nl.txt, reconstructed_nl.txt) - no LLM calls'
    )
    parser.add_argument(
        '--max-repair-iterations',
        type=int,
        default=3,
        help='Maximum repair iterations for SAT cases (default: 3)'
    )
    parser.add_argument(
        '--ablation',
        choices=['full', 'random', 'no_reasoning', 'regenerate'],
        default='full',
        help='Ablation mode: full (default), random (random arrow), no_reasoning (diagnosis without reasoning feedback), regenerate (full T1/T2/T3 rerun from original NL, no diagnosis)'
    )
    parser.add_argument(
        '--provider',
        choices=['openai', 'anthropic'],
        default=None,
        help='LLM provider (overrides model_config.txt setting)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Model name override (e.g., claude-sonnet-4-20250514, gpt-4o)'
    )
    parser.add_argument(
        '--diagnosis-provider',
        choices=['openai', 'anthropic'],
        default=None,
        help='Optional: LLM provider for the diagnosis step only (cross-model diagnosis). '
             'If unset, the diagnosis uses the same provider as the repair step.'
    )
    parser.add_argument(
        '--diagnosis-model',
        type=str,
        default=None,
        help='Optional: Model for the diagnosis step only. Required if --diagnosis-provider is set.'
    )
    parser.add_argument(
        '--ablation-suffix',
        type=str,
        default='',
        help='Optional suffix appended to the ablation output directory (e.g., "_xclaude" '
             'produces repair_full_xclaude/). Useful for cross-model runs to avoid clobbering existing outputs.'
    )
    parser.add_argument(
        '--rules-dir',
        type=str,
        default=None,
        help='Override rules directory. Default: rules-<domain> (e.g., rules-traffic for --domain traffic, rules-wildlife for --domain wildlife). Use rules-test for quick sanity checks.'
    )
    parser.add_argument(
        '--domain',
        choices=['traffic', 'wildlife'],
        default=None,
        help='Domain whose schema and prompts to use, resolved as config/domains/<domain>/. '
             'Default: traffic (preserves prior behavior). For --repair-sat / --analyze-* on '
             'an existing run, the domain is auto-read from <run_dir>/config/domain.txt if '
             'present; --domain explicit always wins.'
    )

    args = parser.parse_args()

    # Directory paths
    base_dir = Path(__file__).parent
    config_dir = base_dir / "config"
    output_dir = base_dir / "output"

    # Resolve domain. For commands that operate on an existing run dir, prefer
    # the domain marker stored in that run's config snapshot. Explicit --domain
    # always wins. Fallback: traffic (preserves prior default behavior).
    def _resolve_domain(run_dir_arg: str = None) -> str:
        if args.domain:
            return args.domain
        if run_dir_arg:
            marker = Path(run_dir_arg) / 'config' / 'domain.txt'
            if marker.exists():
                name = marker.read_text(encoding='utf-8').strip()
                if name in ('traffic', 'wildlife'):
                    return name
        return 'traffic'

    # For --mode (roundtrip / base), domain is resolved without a run_dir.
    # For --analyze-* / --repair-sat paths below, each call site resolves its own.
    domain = _resolve_domain()
    domain_dir = config_dir / "domains" / domain
    if not domain_dir.exists():
        print(f"Error: Domain directory not found: {domain_dir}")
        print(f"Expected layout: config/domains/<domain>/schema.smt2 and config/domains/<domain>/prompts/")
        sys.exit(1)

    # Default rules dir is rules-<domain> unless overridden
    rules_dir = base_dir / (args.rules_dir if args.rules_dir else f"rules-{domain}")
    
    # Handle analysis flags (no LLM calls)
    if args.analyze_smt_pre:
        from src.analysis.smt_analyzer import analyze_smt_pre_repair
        
        run_dir = Path(args.analyze_smt_pre)
        if not run_dir.exists():
            print(f"Error: Run directory not found: {run_dir}")
            sys.exit(1)
        
        # Read schema
        schema_path = run_dir / 'config' / 'schema.smt2'
        if not schema_path.exists():
            print(f"Error: Schema file not found: run directory: {schema_path}")
            sys.exit(1)
        
        with open(schema_path, 'r') as f:
            schema = f.read()
        
        analyze_smt_pre_repair(run_dir, schema)
        return
    
    if args.analyze_nli_pre:
        from src.analysis.nli_analyzer import analyze_nli

        run_dir = Path(args.analyze_nli_pre)
        if not run_dir.exists():
            print(f"Error: Run directory not found: {run_dir}")
            sys.exit(1)

        analyze_nli(run_dir)
        return

    if args.analyze_smt:
        from src.analysis.smt_analyzer import analyze_smt_folder
        
        folder = Path(args.analyze_smt)
        if not folder.exists():
            print(f"Error: Folder not found: {folder}")
            sys.exit(1)
        
        # Need schema — look in the run dir's config, or the project config
        schema = None
        # Walk up from folder to find config/schema.smt2
        # e.g., folder = output/run_XXX/r001/repair_full → run_dir = output/run_XXX
        candidate = folder
        for _ in range(5):
            schema_path = candidate / 'config' / 'schema.smt2'
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    schema = f.read()
                break
            candidate = candidate.parent
        
        if schema is None:
            # Fallback: use the active domain's schema (resolved from --domain or
            # from the folder's nearest run_dir/config/domain.txt marker if any)
            fallback_domain = _resolve_domain(str(folder))
            schema_path = config_dir / "domains" / fallback_domain / 'schema.smt2'
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    schema = f.read()
            else:
                print(f"Error: Could not find schema.smt2 (looked at run-dir snapshot, then {schema_path})")
                sys.exit(1)
        
        analyze_smt_folder(folder, schema)
        return
    
    if args.analyze_nli:
        from src.analysis.nli_analyzer import analyze_nli_folder
        
        folder = Path(args.analyze_nli)
        if not folder.exists():
            print(f"Error: Folder not found: {folder}")
            sys.exit(1)
        
        analyze_nli_folder(folder)
        return
    
    # Handle repair-sat mode (new 3-arrow iterative repair system)
    if args.repair_sat:
        from src.repair.oracle_repair import OracleRepair
        from src.llm_client import LLMClient
        from src.z3_checker import Z3Checker
        from src.file_handler import FileHandler
        import time

        run_dir = Path(args.repair_sat)
        if not run_dir.exists():
            print(f"Error: Run directory not found: {run_dir}")
            sys.exit(1)

        # Resolve domain for THIS repair invocation: explicit --domain > run_dir
        # marker > 'traffic'. The OracleRepair below reads its prompt templates
        # from the resolved domain's prompts/ directory.
        repair_domain = _resolve_domain(str(run_dir))
        repair_domain_dir = config_dir / "domains" / repair_domain
        repair_prompts_dir = repair_domain_dir / "prompts"
        if not repair_prompts_dir.exists():
            print(f"Error: Prompts directory not found: {repair_prompts_dir}")
            sys.exit(1)

        print(f"\nApplying iterative repair to: {run_dir}")
        print(f"Domain: {repair_domain}  (prompts: {repair_prompts_dir})")
        print(f"Max repair iterations: {args.max_repair_iterations}")
        print(f"Ablation mode: {args.ablation}")
        print("="*80)
        
        # Read model config (need provider to determine which API key to load)
        model_config_file = config_dir / "model_config.txt"
        model = "gpt-4o-mini"
        temperature = 0.3
        top_p = 0.9
        request_delay = 10.0
        provider = "openai"
        
        if model_config_file.exists():
            with open(model_config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            if key == 'model':
                                model = value
                            elif key == 'request_delay':
                                request_delay = float(value)
                            elif key == 'provider':
                                provider = value
        
        # CLI flag overrides config file
        if args.provider:
            provider = args.provider
        if args.model:
            model = args.model
        
        # Auto-set model when provider is overridden but model isn't
        if args.provider == 'anthropic' and not args.model and model.startswith('gpt'):
            model = 'claude-opus-4-6'
            print(f"  Auto-selected model: {model} (provider override without --model)")
        elif args.provider == 'openai' and not args.model and model.startswith('claude'):
            model = 'gpt-4o'
            print(f"  Auto-selected model: {model} (provider override without --model)")
        
        # Read API key based on provider
        if provider == 'anthropic':
            api_key_file = config_dir / "anthropic_api_key.txt"
            key_label = "Anthropic"
        else:
            api_key_file = config_dir / "openai_api_key.txt"
            key_label = "OpenAI"
        
        if not api_key_file.exists():
            print(f"Error: {key_label} API key file not found at {api_key_file}")
            print("API key is required for repair (LLM calls).")
            sys.exit(1)
        
        with open(api_key_file, 'r') as f:
            api_key = f.read().strip()
        
        # Read schema from run directory
        schema_path = run_dir / 'config' / 'schema.smt2'
        if not schema_path.exists():
            print(f"Error: Schema file not found in run directory: {schema_path}")
            sys.exit(1)
        
        with open(schema_path, 'r') as f:
            schema = f.read()
        
        # Initialize LLM client, oracle, Z3 checker, and file handler
        print(f"  Provider: {provider}")
        print(f"  Model: {model}")
        print(f"  Ablation: {args.ablation}")
        llm_client = LLMClient(api_key=api_key, model=model, temperature=temperature, top_p=top_p, provider=provider)

        # Optional cross-model diagnosis: a separate LLM client used only for diagnose() calls.
        diagnosis_llm_client = None
        if args.diagnosis_provider:
            if not args.diagnosis_model:
                print("Error: --diagnosis-model is required when --diagnosis-provider is set.")
                sys.exit(1)
            if args.diagnosis_provider == 'anthropic':
                dx_key_file = config_dir / 'anthropic_api_key.txt'
            else:
                dx_key_file = config_dir / 'openai_api_key.txt'
            if not dx_key_file.exists():
                print(f"Error: API key file for diagnosis provider not found at {dx_key_file}")
                sys.exit(1)
            with open(dx_key_file, 'r') as f:
                dx_api_key = f.read().strip()
            print(f"  Diagnosis provider (cross): {args.diagnosis_provider}")
            print(f"  Diagnosis model (cross):    {args.diagnosis_model}")
            diagnosis_llm_client = LLMClient(api_key=dx_api_key, model=args.diagnosis_model,
                                              temperature=temperature, top_p=top_p,
                                              provider=args.diagnosis_provider)

        oracle = OracleRepair(llm_client, schema, repair_prompts_dir, request_delay,
                              max_iterations=args.max_repair_iterations,
                              ablation_mode=args.ablation,
                              diagnosis_llm_client=diagnosis_llm_client)
        z3_checker = Z3Checker()
        file_handler = FileHandler(rules_dir="", domain_dir=str(repair_domain_dir), output_dir="")
        
        # Find all rule directories: any dir containing original_nl.txt that
        # isn't a special directory (config, ablation outputs, etc.). This is
        # domain-agnostic — works for r001/wl001/anything.
        SPECIAL_DIRS = {'config'}
        rule_dirs = [
            d for d in sorted(run_dir.iterdir())
            if d.is_dir()
            and d.name not in SPECIAL_DIRS
            and not d.name.startswith('repair_')
            and (d / 'original_nl.txt').exists()
        ]
        
        # Ablation output subfolder name (with optional suffix for cross-model runs)
        ablation_subdir = f"repair_{args.ablation}{args.ablation_suffix}"
        
        # Create top-level ablation directory
        ablation_root = run_dir / ablation_subdir
        ablation_root.mkdir(parents=True, exist_ok=True)
        
        print(f"Found {len(rule_dirs)} rules to process")
        print(f"Results will be saved to: {ablation_subdir}/<rule>/")
        print("-"*80)
        
        repaired_count = 0
        skipped_count = 0
        success_count = 0
        total_llm_calls = 0
        per_rule_stats = {}
        
        for idx, rule_dir in enumerate(rule_dirs, 1):
            rule_name = rule_dir.name
            print(f"\n[{idx}/{len(rule_dirs)}] Processing: {rule_name}")
            
            # Check if required files exist (iteration_0 structure)
            iteration_0_dir = rule_dir / 'iteration_0'
            if iteration_0_dir.exists():
                # New structure with iterations
                phase1_file = iteration_0_dir / 'encoding_phase1.smt2'
                phase3_file = iteration_0_dir / 'encoding_phase3.smt2'
                reconstructed_nl_file = iteration_0_dir / 'reconstructed_nl.txt'
            else:
                # Old structure (flat)
                phase1_file = rule_dir / 'encoding_phase1.smt2'
                phase3_file = rule_dir / 'encoding_phase3.smt2'
                reconstructed_nl_file = rule_dir / 'reconstructed_nl.txt'
            
            original_nl_file = rule_dir / 'original_nl.txt'
            
            if not all([phase1_file.exists(), phase3_file.exists(), original_nl_file.exists(), reconstructed_nl_file.exists()]):
                print(f"  SKIPPED: Missing required files")
                skipped_count += 1
                continue
            
            # Check initial equivalence
            z3_result = z3_checker.check_equivalence_with_schema(
                phase1_file.read_text(), phase3_file.read_text(), schema
            )
            
            if z3_result['result'] == 'UNSAT':
                print(f"  SKIPPED: Encodings are already equivalent (UNSAT), no repair needed")
                # Copy baseline artifacts to ablation dir so analysis sees all rules
                _ablation_dir = ablation_root / rule_name
                _ablation_dir.mkdir(parents=True, exist_ok=True)
                import shutil
                for _fname, _src in [('encoding_phase1.smt2', phase1_file), 
                                      ('encoding_phase3.smt2', phase3_file),
                                      ('reconstructed_nl.txt', reconstructed_nl_file),
                                      ('original_nl.txt', original_nl_file)]:
                    if _src.exists():
                        shutil.copy2(_src, _ablation_dir / _fname)
                # Write z3 result
                with open(_ablation_dir / 'z3_result.txt', 'w') as _f:
                    _f.write("Result: UNSAT\n")
                per_rule_stats[rule_name] = {
                    'pre_repair': 'UNSAT',
                    'post_repair': 'UNSAT',
                    'iterations': 0,
                    'llm_calls': 0,
                    'arrows_repaired': []
                }
                skipped_count += 1
                continue
            elif z3_result['result'] != 'SAT':
                print(f"  SKIPPED: Cannot determine equivalence ({z3_result['result']})")
                skipped_count += 1
                continue
            
            # Only proceed for SAT cases
            print(f"  Status: SAT - Starting iterative repair...")
            print(f"  Initial counterexample: {z3_result['counterexample']}")
            
            # Read all initial artifacts
            original_nl = original_nl_file.read_text().strip()
            phase1_smt = phase1_file.read_text().strip()
            reconstructed_nl = reconstructed_nl_file.read_text().strip()
            phase3_smt = phase3_file.read_text().strip()
            
            # If iteration_0 doesn't exist, create it and save initial state
            if not iteration_0_dir.exists():
                iteration_0_dir = file_handler.create_iteration_directory(rule_dir, 0)
                file_handler.save_iteration_artifacts(
                    iteration_0_dir, phase1_smt, reconstructed_nl, phase3_smt, z3_result
                )
            
            # Reset per-rule LLM call counter
            oracle.llm_call_counter = 0
            
            # Run full repair process
            repair_result = oracle.run_full_repair(
                original_nl, phase1_smt, reconstructed_nl, 
                phase3_smt, z3_result['counterexample'], z3_checker, schema
            )
            
            # Save results to ablation-specific subdirectory
            ablation_dir = ablation_root / rule_name
            ablation_dir.mkdir(parents=True, exist_ok=True)
            
            for iter_num, iter_result in enumerate(repair_result['iterations'], 1):
                if not iter_result['success']:
                    continue
                
                # Create iteration directory inside ablation subdir
                iteration_dir = ablation_dir / f"iteration_{iter_num}"
                iteration_dir.mkdir(parents=True, exist_ok=True)
                
                # Diagnosis + repair only exist for full / no_reasoning / random.
                # In 'regenerate' there is no diagnosis call and no scoped repair operator,
                # so repaired_arrow is None and we skip these saves.
                if iter_result.get('repaired_arrow') is not None:
                    # Save diagnosis
                    file_handler.save_diagnosis(
                        iteration_dir,
                        iter_result['diagnosis'],
                        "",  # Prompt not saved in result (would be too large)
                        iter_result['diagnosis'].get('raw_response', '')
                    )

                    # Save repair
                    file_handler.save_repair(
                        iteration_dir,
                        iter_result['repaired_arrow'],
                        iter_result.get('repair_prompt', ''),
                        iter_result['repair_response'],
                        iter_result['repair_response']
                    )
                
                # Save regenerations (if any)
                regen_prompts = iter_result.get('regeneration_prompts', {})
                regen_responses = iter_result.get('regeneration_responses', {})
                
                for arrow_key in regen_prompts:
                    # arrow_key is like 'arrow_2' or 'arrow_3'
                    arrow_num = int(arrow_key.split('_')[1])
                    file_handler.save_regeneration(
                        iteration_dir,
                        arrow_num,
                        regen_prompts[arrow_key],
                        regen_responses[arrow_key],
                        regen_responses[arrow_key]
                    )
                
                # Check Z3 equivalence for this iteration
                iter_z3 = z3_checker.check_equivalence_with_schema(
                    iter_result['phase1_smt'],
                    iter_result['phase3_smt'],
                    schema
                )
                
                # Save iteration artifacts
                file_handler.save_iteration_artifacts(
                    iteration_dir,
                    iter_result['phase1_smt'],
                    iter_result['reconstructed_nl'],
                    iter_result['phase3_smt'],
                    iter_z3
                )
            
            # Save repair summary to ablation dir
            file_handler.save_repair_summary(
                ablation_dir,
                repair_result['iterations'],
                repair_result['final_equivalent'],
                repair_result['total_iterations']
            )
            
            # Also copy final artifacts to ablation dir root for easy analysis
            # (encoding_phase1.smt2, reconstructed_nl.txt, encoding_phase3.smt2, original_nl.txt)
            final_iter_idx = len(repair_result['iterations'])
            final_iter_dir = ablation_dir / f"iteration_{final_iter_idx}"
            if final_iter_dir.exists():
                for fname in ['encoding_phase1.smt2', 'reconstructed_nl.txt', 'encoding_phase3.smt2']:
                    src = final_iter_dir / fname
                    if src.exists():
                        import shutil
                        shutil.copy2(src, ablation_dir / fname)
            
            # Copy original_nl.txt from rule_dir for NLI analysis
            orig_nl_src = rule_dir / 'original_nl.txt'
            if orig_nl_src.exists():
                import shutil
                shutil.copy2(orig_nl_src, ablation_dir / 'original_nl.txt')
            
            # Track per-rule stats
            rule_llm_calls = oracle.llm_call_counter
            total_llm_calls += rule_llm_calls
            per_rule_stats[rule_name] = {
                'pre_repair': 'SAT',
                'post_repair': 'UNSAT' if repair_result['final_equivalent'] else 'SAT',
                'iterations': repair_result['total_iterations'],
                'llm_calls': rule_llm_calls,
                'arrows_repaired': [iter_r.get('repaired_arrow') for iter_r in repair_result['iterations'] if iter_r.get('success')]
            }
            
            if repair_result['final_equivalent']:
                print(f"  SUCCESS: Achieved equivalence after {repair_result['total_iterations']} iteration(s)")
                success_count += 1
            else:
                print(f"  PARTIAL: Exhausted {repair_result['total_iterations']} iterations without achieving equivalence")
            
            repaired_count += 1
            
            # Delay before next rule
            if idx < len(rule_dirs):
                time.sleep(request_delay)
        
        print("\n" + "="*80)
        print(f"Iterative repair complete! (mode: {args.ablation})")
        print("="*80)
        print(f"\nSummary:")
        print(f"  Total rules: {len(rule_dirs)}")
        print(f"  Attempted repair: {repaired_count}")
        print(f"  Achieved equivalence: {success_count}")
        print(f"  Skipped: {skipped_count}")
        print(f"  Total LLM calls: {total_llm_calls}")
        if success_count > 0:
            print(f"  LLM calls per UNSAT gained: {total_llm_calls / success_count:.1f}")
        print(f"\nResults saved to: {ablation_subdir}/<rule>/")
        
        # Save repair_stats.json for this ablation
        stats = {
            'ablation_mode': args.ablation,
            'max_iterations': args.max_repair_iterations,
            'model': model,
            'provider': provider,
            'total_rules': len(rule_dirs),
            'attempted_repair': repaired_count,
            'achieved_unsat': success_count,
            'skipped': skipped_count,
            'total_llm_calls': total_llm_calls,
            'llm_calls_per_unsat': round(total_llm_calls / success_count, 2) if success_count > 0 else None,
            'repair_rate': round(success_count / repaired_count * 100, 1) if repaired_count > 0 else 0,
            'per_rule': per_rule_stats
        }
        
        stats_path = run_dir / f"repair_stats_{args.ablation}{args.ablation_suffix}.json"
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"  Stats saved to: {stats_path}")
        return
    
    # Read model config
    model_config_file = config_dir / "model_config.txt"
    model = "gpt-4o-mini"  # Default
    temperature = 0.3  # Default
    top_p = 1.0  # Default
    request_delay = 0.5  # Default (0.5 seconds between requests)
    provider = "openai"  # Default
    
    if model_config_file.exists():
        with open(model_config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if key == 'model':
                            model = value
                        elif key == 'temperature':
                            temperature = float(value)
                        elif key == 'top_p':
                            top_p = float(value)
                        elif key == 'request_delay':
                            request_delay = float(value)
                        elif key == 'provider':
                            provider = value
    
    # CLI flag overrides config file
    if args.provider:
        provider = args.provider
    if args.model:
        model = args.model
    
    # Auto-set model when provider is overridden but model isn't
    if args.provider == 'anthropic' and not args.model and model.startswith('gpt'):
        model = 'claude-opus-4-6'
        print(f"Auto-selected model: {model} (provider override without --model)")
    elif args.provider == 'openai' and not args.model and model.startswith('claude'):
        model = 'gpt-4o'
        print(f"Auto-selected model: {model} (provider override without --model)")
    
    # Read API key based on provider
    if provider == 'anthropic':
        api_key_file = config_dir / "anthropic_api_key.txt"
        key_label = "Anthropic"
    else:
        api_key_file = config_dir / "openai_api_key.txt"
        key_label = "OpenAI"
    
    if not api_key_file.exists():
        print(f"Error: {key_label} API key file not found at {api_key_file}")
        print(f"Please create the file and add your {key_label} API key.")
        sys.exit(1)
    
    with open(api_key_file, 'r') as f:
        api_key = f.read().strip()
    
    if not api_key:
        print(f"Error: API key is empty in {api_key_file}")
        sys.exit(1)
    
    # Run selected mode
    try:
        run_roundtrip_mode(domain_dir, rules_dir, output_dir, api_key, model,
                           temperature, top_p, args.max_repair_attempts, request_delay,
                           provider)
    except Exception as e:
        print(f"Error during processing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
