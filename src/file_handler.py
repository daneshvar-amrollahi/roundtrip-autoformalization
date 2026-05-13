"""
File handling utilities for reading inputs and writing outputs.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
import shutil


class FileHandler:
    """Handles all file I/O operations."""

    def __init__(self, rules_dir: str, domain_dir: str, output_dir: str):
        """
        Initialize file handler with directory paths.

        Args:
            rules_dir: Directory containing NL rule files
            domain_dir: Domain config directory (e.g., config/domains/traffic).
                        Must contain schema.smt2 and a prompts/ subdir.
            output_dir: Base directory for output
        """
        self.rules_dir = Path(rules_dir)
        self.domain_dir = Path(domain_dir)
        self.prompts_dir = self.domain_dir / "prompts"
        self.output_dir = Path(output_dir)

    def read_schema(self) -> str:
        """Read the domain's schema.smt2."""
        with open(self.domain_dir / 'schema.smt2', 'r', encoding='utf-8') as f:
            return f.read()

    def read_prompt(self, name: str) -> str:
        """Read a prompt template from the domain's prompts/ directory."""
        with open(self.prompts_dir / name, 'r', encoding='utf-8') as f:
            return f.read()

    def read_config_file(self, filename: str) -> str:
        """
        Back-compat shim: dispatch to read_schema / read_prompt by filename.

        - schema.smt2 → read_schema
        - everything else (prompt .txt files) → read_prompt
        """
        if filename == 'schema.smt2':
            return self.read_schema()
        return self.read_prompt(filename)
    
    def get_rule_files(self) -> List[Path]:
        """
        Get all rule files from rules directory.
        
        Returns:
            List of Path objects for rule files
        """
        if not self.rules_dir.exists():
            return []
        
        # Get all .txt files (or you can adjust the pattern)
        return sorted(self.rules_dir.glob('*.txt'))
    
    def read_rule_file(self, filepath: Path) -> str:
        """
        Read a rule file.
        
        Args:
            filepath: Path to rule file
            
        Returns:
            Rule content as string
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def create_run_directory(self) -> Path:
        """
        Create a timestamped run directory.
        
        Returns:
            Path to the created run directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = self.output_dir / f"run_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir
    
    def copy_config_to_run(self, run_dir: Path) -> None:
        """
        Snapshot the active domain config (schema + all prompts) into the run
        directory for reproducibility. The snapshot stays flat so existing
        analysis paths (which expect <run_dir>/config/schema.smt2 and
        <run_dir>/config/<prompt>.txt) keep working unchanged.

        Also writes <run_dir>/config/domain.txt naming the source domain, so
        downstream commands like --repair-sat are self-describing.
        """
        config_backup_dir = run_dir / "config"
        config_backup_dir.mkdir(exist_ok=True)

        # Schema
        schema_src = self.domain_dir / 'schema.smt2'
        if schema_src.exists():
            shutil.copy2(schema_src, config_backup_dir / 'schema.smt2')

        # All prompt templates (.txt files under prompts/)
        if self.prompts_dir.exists():
            for prompt_path in sorted(self.prompts_dir.glob('*.txt')):
                shutil.copy2(prompt_path, config_backup_dir / prompt_path.name)

        # Domain marker for self-describing runs
        (config_backup_dir / 'domain.txt').write_text(self.domain_dir.name + '\n', encoding='utf-8')
    
    def write_smt_output(self, run_dir: Path, rule_filename: str, smt_content: str, encoding_num: int) -> None:
        """
        Write SMT output to file.
        
        Args:
            run_dir: Path to run directory
            rule_filename: Original rule filename
            smt_content: SMT formalization content
            encoding_num: Encoding number (1, 2, 3, ...)
        """
        # Create a folder for this rule
        rule_name = Path(rule_filename).stem
        rule_folder = run_dir / rule_name
        rule_folder.mkdir(exist_ok=True)
        
        # Write encoding file
        encoding_filename = f"encoding_{encoding_num}.smt2"
        output_path = rule_folder / encoding_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(smt_content)
    
    def create_iteration_directory(self, rule_dir: Path, iteration_num: int) -> Path:
        """
        Create an iteration directory for repair process.
        
        Args:
            rule_dir: Path to rule directory
            iteration_num: Iteration number (0 for initial, 1+ for repairs)
            
        Returns:
            Path to the created iteration directory
        """
        iteration_dir = rule_dir / f"iteration_{iteration_num}"
        iteration_dir.mkdir(parents=True, exist_ok=True)
        return iteration_dir
    
    def save_iteration_artifacts(self, iteration_dir: Path, phase1_smt: str, 
                                reconstructed_nl: str, phase3_smt: str, 
                                z3_result: dict) -> None:
        """
        Save all artifacts for an iteration.
        
        Args:
            iteration_dir: Path to iteration directory
            phase1_smt: Phase 1 SMT encoding
            reconstructed_nl: Reconstructed natural language
            phase3_smt: Phase 3 SMT encoding
            z3_result: Z3 equivalence check result
        """
        # Save Phase 1 encoding
        with open(iteration_dir / 'encoding_phase1.smt2', 'w') as f:
            f.write(phase1_smt)
        
        # Save reconstructed NL
        with open(iteration_dir / 'reconstructed_nl.txt', 'w') as f:
            f.write(reconstructed_nl)
        
        # Save Phase 3 encoding
        with open(iteration_dir / 'encoding_phase3.smt2', 'w') as f:
            f.write(phase3_smt)
        
        # Save Z3 result
        with open(iteration_dir / 'z3_result.txt', 'w') as f:
            f.write(f"Result: {z3_result.get('result', 'UNKNOWN')}\n")
            if z3_result.get('counterexample'):
                f.write(f"Counterexample: {z3_result['counterexample']}\n")
    
    def save_diagnosis(self, iteration_dir: Path, diagnosis: dict, 
                      diagnosis_prompt: str, diagnosis_response: str) -> None:
        """
        Save diagnosis results for an iteration.
        
        Args:
            iteration_dir: Path to iteration directory
            diagnosis: Parsed diagnosis dict with 'failed_arrow' and 'reasoning'
            diagnosis_prompt: Full prompt sent to LLM
            diagnosis_response: Full LLM response
        """
        diagnosis_file = iteration_dir / 'diagnosis.txt'
        with open(diagnosis_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("DIAGNOSIS\n")
            f.write("="*80 + "\n\n")
            f.write(f"First Failed Arrow: {diagnosis.get('first_failed_arrow', 'Unknown')}\n\n")
            f.write("Reasoning:\n")
            f.write(diagnosis.get('reasoning', 'No reasoning provided'))
            f.write("\n\n" + "="*80 + "\n")
            f.write("FULL LLM RESPONSE\n")
            f.write("="*80 + "\n\n")
            f.write(diagnosis_response)
    
    def save_repair(self, iteration_dir: Path, arrow_num: int, 
                   repair_prompt: str, repair_response: str, 
                   repaired_output: str) -> None:
        """
        Save repair results for a specific arrow.
        
        Args:
            iteration_dir: Path to iteration directory
            arrow_num: Arrow number that was repaired (1, 2, or 3)
            repair_prompt: Full prompt sent to LLM for repair
            repair_response: Full LLM response
            repaired_output: Extracted repaired output (SMT or NL)
        """
        repair_dir = iteration_dir / f"repair_arrow_{arrow_num}"
        repair_dir.mkdir(exist_ok=True)
        
        # Save prompt
        with open(repair_dir / 'prompt.txt', 'w') as f:
            f.write(repair_prompt)
        
        # Save full response
        with open(repair_dir / 'response.txt', 'w') as f:
            f.write(repair_response)
        
        # Save extracted output
        if arrow_num == 2:
            # Arrow 2 produces NL
            output_file = repair_dir / 'repaired_output.txt'
        else:
            # Arrows 1 and 3 produce SMT
            output_file = repair_dir / 'repaired_output.smt2'
        
        with open(output_file, 'w') as f:
            f.write(repaired_output)
    
    def save_regeneration(self, iteration_dir: Path, arrow_num: int,
                         regen_prompt: str, regen_response: str,
                         regenerated_output: str) -> None:
        """
        Save regeneration results for a downstream arrow.
        
        Args:
            iteration_dir: Path to iteration directory
            arrow_num: Arrow number that was regenerated (2 or 3)
            regen_prompt: Full prompt sent to LLM for regeneration
            regen_response: Full LLM response
            regenerated_output: Extracted regenerated output (SMT or NL)
        """
        regen_dir = iteration_dir / f"regenerate_arrow_{arrow_num}"
        regen_dir.mkdir(exist_ok=True)
        
        # Save prompt
        with open(regen_dir / 'prompt.txt', 'w') as f:
            f.write(regen_prompt)
        
        # Save full response
        with open(regen_dir / 'response.txt', 'w') as f:
            f.write(regen_response)
        
        # Save extracted output
        if arrow_num == 2:
            # Arrow 2 produces NL
            output_file = regen_dir / 'regenerated_output.txt'
        else:
            # Arrow 3 produces SMT
            output_file = regen_dir / 'regenerated_output.smt2'
        
        with open(output_file, 'w') as f:
            f.write(regenerated_output)
    
    def save_repair_summary(self, rule_dir: Path, iterations: list, 
                           final_equivalent: bool, total_iterations: int) -> None:
        """
        Save a summary of the entire repair process.
        
        Args:
            rule_dir: Path to rule directory
            iterations: List of iteration result dicts
            final_equivalent: Whether final encodings are equivalent
            total_iterations: Total number of iterations performed
        """
        summary_file = rule_dir / 'repair_summary.txt'
        with open(summary_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("REPAIR SUMMARY\n")
            f.write("="*80 + "\n\n")
            f.write(f"Total Iterations: {total_iterations}\n")
            f.write(f"Final Result: {'EQUIVALENT (UNSAT)' if final_equivalent else 'NOT EQUIVALENT (SAT)'}\n\n")
            
            for idx, iter_result in enumerate(iterations, 1):
                f.write("-"*80 + "\n")
                f.write(f"Iteration {idx}\n")
                f.write("-"*80 + "\n")
                
                if iter_result.get('success'):
                    diagnosis = iter_result.get('diagnosis', {})
                    f.write(f"Failed Arrow: {diagnosis.get('first_failed_arrow', 'Unknown')}\n")
                    f.write(f"Repaired Arrow: {iter_result.get('repaired_arrow', 'Unknown')}\n")
                    
                    # Show which arrows were regenerated
                    regen = iter_result.get('regeneration_responses', {})
                    if regen:
                        f.write(f"Regenerated Arrows: {', '.join(regen.keys())}\n")
                else:
                    f.write("Status: Failed to diagnose/repair\n")
                
                f.write("\n")
            
            f.write("="*80 + "\n")
