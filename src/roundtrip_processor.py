"""
Roundtrip processor for NL → SMT → NL → SMT pipeline with schema awareness.
"""

import time
from pathlib import Path
from .llm_client import LLMClient
from .file_handler import FileHandler
from .repair.encoding_repairer import EncodingRepairer


class RoundtripProcessor:
    """Orchestrates the roundtrip translation pipeline with schema checking."""
    
    def __init__(self, llm_client: LLMClient, file_handler: FileHandler, 
                 max_repair_attempts: int = 5, request_delay: float = 0.5):
        """
        Initialize roundtrip processor.
        
        Args:
            llm_client: LLM client for API calls
            file_handler: File handler for I/O operations
            max_repair_attempts: Maximum attempts to repair malformed encodings
            request_delay: Delay in seconds between API requests
        """
        self.llm_client = llm_client
        self.file_handler = file_handler
        self.max_repair_attempts = max_repair_attempts
        self.request_delay = request_delay
        self.repairer = None
    
    def process_all_rules(self, prompt_file: str = 'roundtrip_promptNL2SMT.txt') -> Path:
        """
        Process all NL rules through roundtrip: NL → SMT → NL.
        
        Phase 1: Generates SMT encodings with schema awareness
        Phase 2: Translates successful SMT encodings back to NL
        
        Args:
            prompt_file: Name of prompt file to use for NL→SMT
            
        Returns:
            Path to the run directory
        """
        # Read configuration
        prompt = self.file_handler.read_config_file(prompt_file)
        schema = self.file_handler.read_config_file('schema.smt2')
        
        # Combine prompt and schema into system prompt
        system_prompt = f"{prompt}\n\n{schema}"
        
        # Create run directory and backup config
        run_dir = self.file_handler.create_run_directory()
        self.file_handler.copy_config_to_run(run_dir)
        
        # Create pipeline log file
        pipeline_log = run_dir / "pipeline.log"
        pipeline_log.touch()
        
        # Initialize repairer with schema and log file
        self.repairer = EncodingRepairer(
            llm_client=self.llm_client,
            schema_content=schema,
            max_attempts=self.max_repair_attempts,
            log_file=pipeline_log,
            request_delay=self.request_delay
        )
        
        print(f"Created run directory: {run_dir}")
        
        # Get all rule files
        rule_files = self.file_handler.get_rule_files()
        
        if not rule_files:
            print("No rule files found in rules directory.")
            return run_dir
        
        # ===== PHASE 1: NL → SMT =====
        print(f"\n{'='*60}")
        print("PHASE 1: NL → SMT Encoding")
        print(f"{'='*60}")
        print(f"Processing {len(rule_files)} rule(s)...\n")
        
        # Process each rule
        for rule_file in rule_files:
            print(f"  Processing: {rule_file.name}")
            
            # Log to pipeline.log for context
            with open(pipeline_log, 'a') as f:
                f.write(f"\n{'='*80}\nPHASE 1 - Processing: {rule_file.name}\n{'='*80}\n")
            
            rule_name = rule_file.stem
            rule_dir = run_dir / rule_name
            rule_dir.mkdir(exist_ok=True)
            
            # Copy original NL rule for comparison
            original_nl_file = rule_dir / "original_nl.txt"
            with open(rule_file, 'r') as src, open(original_nl_file, 'w') as dst:
                dst.write(src.read())
            
            # Read rule
            nl_rule = self.file_handler.read_rule_file(rule_file)
            
            # Generate encoding with schema awareness
            try:
                self._process_single_rule(nl_rule, rule_name, rule_dir, system_prompt, pipeline_log)
            except Exception as e:
                print(f"      ✗ Error processing {rule_file.name}: {e}")
                with open(pipeline_log, 'a') as f:
                    f.write(f"      ✗ ERROR: {e}\n")
                continue
        
        # ===== PHASE 2: SMT → NL =====
        print(f"\n{'='*60}")
        print("PHASE 2: SMT → NL Translation")
        print(f"{'='*60}\n")
        
        self._phase2_smt_to_nl(run_dir, rule_files, schema, pipeline_log)
        
        # ===== PHASE 3: Reconstructed NL → SMT =====
        print(f"\n{'='*60}")
        print("PHASE 3: Reconstructed NL → SMT Encoding")
        print(f"{'='*60}\n")
        
        self._phase3_nl_to_smt(run_dir, rule_files, system_prompt, pipeline_log)
        
        # ===== CREATE ITERATION_0 BASELINE =====
        # Save pre-repair state to iteration_0 for all rules
        print(f"\n{'='*60}")
        print("Creating iteration_0 baseline directories...")
        print(f"{'='*60}\n")
        
        from .z3_checker import Z3Checker
        z3_checker = Z3Checker()
        
        for rule_file in rule_files:
            rule_name = rule_file.stem
            rule_dir = run_dir / rule_name
            
            # Check if all files exist
            phase1_file = rule_dir / 'encoding_phase1.smt2'
            phase3_file = rule_dir / 'encoding_phase3.smt2'
            reconstructed_nl_file = rule_dir / 'reconstructed_nl.txt'
            
            if not (phase1_file.exists() and phase3_file.exists() and reconstructed_nl_file.exists()):
                # Skip rules with schema issues or incomplete roundtrip
                continue
            
            # Read the files
            with open(phase1_file, 'r') as f:
                phase1_smt = f.read()
            with open(phase3_file, 'r') as f:
                phase3_smt = f.read()
            with open(reconstructed_nl_file, 'r') as f:
                reconstructed_nl = f.read()
            
            # Run Z3 check for baseline
            z3_result = z3_checker.check_equivalence_with_schema(phase1_smt, phase3_smt, schema)
            
            # Create iteration_0 directory
            iteration_0_dir = self.file_handler.create_iteration_directory(rule_dir, 0)
            
            # Save baseline artifacts
            self.file_handler.save_iteration_artifacts(
                iteration_0_dir,
                phase1_smt,
                reconstructed_nl,
                phase3_smt,
                z3_result
            )
            
            print(f"  ✓ Created iteration_0 for {rule_name}")
        
        print(f"\nRoundtrip completed! Output saved to: {run_dir}")
        print(f"\nRun analysis with:")
        print(f"  python main.py --analyze-smt-pre {run_dir}")
        print(f"  python main.py --analyze-nli {run_dir}")
        return run_dir
    
    def _process_single_rule(self, nl_rule: str, rule_name: str, rule_dir: Path, 
                            system_prompt: str, pipeline_log: Path) -> None:
        """
        Process a single rule with schema checking and repair.
        
        Args:
            nl_rule: Natural language rule text
            rule_name: Name of the rule
            rule_dir: Directory for this rule's output
            system_prompt: Combined prompt and schema
            pipeline_log: Path to repair log file
        """
        print(f"    Generating encoding...")
        
        # Log to pipeline.log
        with open(pipeline_log, 'a') as f:
            f.write(f"    Generating encoding...\n")
        
        # Translate to SMT
        smt_output = self.llm_client.translate_to_smt(nl_rule, system_prompt)
        
        # Rate limiting
        time.sleep(self.request_delay)
        
        # Check if LLM flagged schema insufficiency
        if self._is_schema_insufficient(smt_output):
            explanation = self._extract_schema_issue(smt_output)
            print(f"      ⚠ Schema flagged as insufficient")
            
            # Save to schema_issue_phase1.txt
            schema_issue_file = rule_dir / "schema_issue_phase1.txt"
            with open(schema_issue_file, 'w') as f:
                f.write(explanation)
            
            # Log to pipeline.log
            with open(pipeline_log, 'a') as f:
                f.write(f"      ⚠ Schema insufficient (Phase 1): {explanation}\n")
            
            return
        
        # Schema is sufficient, proceed with repair/validation
        success, repaired_output, errors = self.repairer.repair_encoding(
            encoding=smt_output,
            rule_name=rule_name,
            encoding_num=1,
            output_dir=rule_dir
        )
        
        # Save final encoding as encoding_phase1.smt2
        encoding_file = rule_dir / "encoding_phase1.smt2"
        with open(encoding_file, 'w') as f:
            f.write(repaired_output)
    
    def _is_schema_insufficient(self, output: str) -> bool:
        """
        Check if LLM flagged schema as insufficient.
        
        Args:
            output: LLM response
            
        Returns:
            True if schema was flagged as insufficient
        """
        return output.strip().startswith("SCHEMA_INSUFFICIENT:")
    
    def _extract_schema_issue(self, output: str) -> str:
        """
        Extract schema insufficiency explanation.
        
        Args:
            output: LLM response with SCHEMA_INSUFFICIENT marker
            
        Returns:
            Explanation text
        """
        if output.strip().startswith("SCHEMA_INSUFFICIENT:"):
            # Remove marker and return explanation
            return output.strip()[len("SCHEMA_INSUFFICIENT:"):].strip()
        return output.strip()
    
    def _phase2_smt_to_nl(self, run_dir: Path, rule_files: list, schema: str, pipeline_log: Path) -> None:
        """
        Phase 2: Translate SMT encodings back to natural language.
        
        Args:
            run_dir: Run directory containing rule subdirectories
            rule_files: List of original rule files
            schema: Schema content
            pipeline_log: Path to repair log
        """
        # Read SMT→NL prompt
        smt2nl_prompt = self.file_handler.read_config_file('roundtrip_promptSMT2NL.txt')
        system_prompt = f"{smt2nl_prompt}\n\n{schema}"
        
        successful_count = 0
        skipped_count = 0
        
        for rule_file in rule_files:
            rule_name = rule_file.stem
            rule_dir = run_dir / rule_name
            
            # Check if encoding exists (skip if schema_issue_phase1.txt exists)
            encoding_file = rule_dir / "encoding_phase1.smt2"
            schema_issue_file = rule_dir / "schema_issue_phase1.txt"
            
            if schema_issue_file.exists():
                print(f"  Skipping {rule_file.name} (schema insufficient in Phase 1)")
                skipped_count += 1
                continue
            
            if not encoding_file.exists():
                print(f"  Skipping {rule_file.name} (no encoding found)")
                skipped_count += 1
                continue
            
            print(f"  Translating SMT→NL: {rule_file.name}")
            
            # Log to pipeline.log
            with open(pipeline_log, 'a') as f:
                f.write(f"\n{'='*80}\nPHASE 2 - Translating: {rule_file.name}\n{'='*80}\n")
            
            # Read SMT encoding
            with open(encoding_file, 'r') as f:
                smt_formula = f.read()
            
            # Translate SMT to NL
            try:
                reconstructed_nl = self.llm_client.translate_to_nl(smt_formula, system_prompt)
            except Exception as e:
                print(f"    ✗ Error translating {rule_file.name}: {e}")
                with open(pipeline_log, 'a') as f:
                    f.write(f"      ✗ ERROR (Phase 2): {e}\n")
                skipped_count += 1
                continue
            
            # Rate limiting
            time.sleep(self.request_delay)
            
            # Save reconstructed NL
            reconstructed_nl_file = rule_dir / "reconstructed_nl.txt"
            with open(reconstructed_nl_file, 'w') as f:
                f.write(reconstructed_nl)
            
            print(f"    ✓ Saved to reconstructed_nl.txt")
            successful_count += 1
        
        print(f"\nPhase 2 complete: {successful_count} translated, {skipped_count} skipped")
    
    def _phase3_nl_to_smt(self, run_dir: Path, rule_files: list, system_prompt: str, pipeline_log: Path) -> None:
        """
        Phase 3: Encode reconstructed NL back to SMT.
        
        Args:
            run_dir: Run directory containing rule subdirectories
            rule_files: List of original rule files
            system_prompt: System prompt with NL→SMT instructions and schema
            pipeline_log: Path to repair log
        """
        successful_count = 0
        skipped_count = 0
        schema_issue_count = 0
        
        for rule_file in rule_files:
            rule_name = rule_file.stem
            rule_dir = run_dir / rule_name
            
            # Skip if Phase 1 had schema issue (no reconstructed NL exists)
            schema_issue_phase1 = rule_dir / "schema_issue_phase1.txt"
            if schema_issue_phase1.exists():
                print(f"  Skipping {rule_file.name} (Phase 1 schema issue)")
                skipped_count += 1
                continue
            
            # Check if reconstructed NL exists
            reconstructed_nl_file = rule_dir / "reconstructed_nl.txt"
            if not reconstructed_nl_file.exists():
                print(f"  Skipping {rule_file.name} (no reconstructed NL)")
                skipped_count += 1
                continue
            
            print(f"  Encoding: {rule_file.name}")
            
            # Log to pipeline.log
            with open(pipeline_log, 'a') as f:
                f.write(f"\n{'='*80}\nPHASE 3 - Encoding: {rule_file.name}\n{'='*80}\n")
            
            # Read reconstructed NL
            with open(reconstructed_nl_file, 'r') as f:
                reconstructed_nl = f.read()
            
            # Generate SMT encoding
            try:
                smt_output = self.llm_client.translate_to_smt(reconstructed_nl, system_prompt)
            except Exception as e:
                print(f"    ✗ Error encoding {rule_file.name}: {e}")
                with open(pipeline_log, 'a') as f:
                    f.write(f"      ✗ ERROR (Phase 3): {e}\n")
                skipped_count += 1
                continue
            
            # Rate limiting
            time.sleep(self.request_delay)
            
            # Check if LLM flagged schema insufficiency
            if self._is_schema_insufficient(smt_output):
                explanation = self._extract_schema_issue(smt_output)
                print(f"    ⚠ Schema flagged as insufficient (Phase 3)")
                
                # Save to schema_issue_phase3.txt
                schema_issue_file = rule_dir / "schema_issue_phase3.txt"
                with open(schema_issue_file, 'w') as f:
                    f.write(explanation)
                
                # Log to pipeline.log
                with open(pipeline_log, 'a') as f:
                    f.write(f"      ⚠ Schema insufficient (Phase 3): {explanation}\n")
                
                schema_issue_count += 1
                continue
            
            # Schema is sufficient, proceed with repair/validation
            success, repaired_output, errors = self.repairer.repair_encoding(
                encoding=smt_output,
                rule_name=f"{rule_name}_phase3",
                encoding_num=3,
                output_dir=rule_dir
            )
            
            # Save final encoding as encoding_phase3.smt2
            encoding_file = rule_dir / "encoding_phase3.smt2"
            with open(encoding_file, 'w') as f:
                f.write(repaired_output)
            
            print(f"    ✓ Saved to encoding_phase3.smt2")
            successful_count += 1
        
        print(f"\nPhase 3 complete: {successful_count} encoded, {schema_issue_count} schema issues, {skipped_count} skipped")
