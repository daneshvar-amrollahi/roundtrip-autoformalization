"""
Iterative repair for SAT cases in roundtrip mode.

When Phase 1 and Phase 3 encodings are not equivalent (Z3 returns SAT),
the system uses a 3-arrow diagnosis and repair approach:
- Arrow 1: Original NL → Phase 1 SMT
- Arrow 2: Phase 1 SMT → Reconstructed NL
- Arrow 3: Reconstructed NL → Phase 3 SMT

The repair process:
1. Diagnose which arrow FIRST failed
2. Repair that arrow with targeted feedback
3. Re-run downstream arrows
4. Check equivalence again
5. Repeat until UNSAT or max iterations reached
"""

import time
from pathlib import Path
from typing import Dict, Optional, Tuple
from ..llm_client import LLMClient


class OracleRepair:
    """Iterative arrow-based repair system for SAT cases."""
    
    def __init__(self, llm_client: LLMClient, schema_content: str, prompts_dir,
                 request_delay: float = 10.0, max_iterations: int = 3,
                 ablation_mode: str = 'full',
                 diagnosis_llm_client: Optional[LLMClient] = None):
        """
        Initialize the iterative repair system.

        Args:
            llm_client: LLM client for API calls (used for repair / regeneration)
            schema_content: SMT schema content
            prompts_dir: Directory containing the six prompt templates used by
                         repair (diagnosis_prompt.txt, repair_arrow{1,2,3}_prompt.txt,
                         roundtrip_prompt{NL2SMT,SMT2NL}.txt). Caller is
                         responsible for resolving this from --domain.
            request_delay: Delay in seconds between API requests
            max_iterations: Maximum number of repair iterations (default: 3)
            ablation_mode: One of 'full', 'random', 'no_reasoning', 'regenerate'
                - 'full': Full diagnosis with reasoning passed to repair (default)
                - 'random': Skip diagnosis, pick arrow uniformly at random
                - 'no_reasoning': Full diagnosis but reasoning NOT passed to repair
                - 'regenerate': No diagnosis, no scoped repair. Re-run T1, T2, T3 from
                  original_nl from scratch each iteration. Tests whether localized
                  repair beats blind resampling of the whole pipeline.
            diagnosis_llm_client: Optional separate LLM client for the diagnosis
                step only. If None, the same `llm_client` is used for both diagnosis
                and repair. Setting this enables cross-model diagnosis (e.g., GPT
                pipeline + Claude judge + GPT repair).
        """
        self.llm_client = llm_client
        self.diagnosis_llm_client = diagnosis_llm_client if diagnosis_llm_client is not None else llm_client
        self.schema_content = schema_content
        self.prompts_dir = Path(prompts_dir)
        self.request_delay = request_delay
        self.max_iterations = max_iterations
        self.ablation_mode = ablation_mode
        self.llm_call_counter = 0

        # Load all prompt templates from the caller-supplied prompts dir
        self.templates = {}

        template_files = {
            'diagnosis': 'diagnosis_prompt.txt',
            'repair_arrow1': 'repair_arrow1_prompt.txt',
            'repair_arrow2': 'repair_arrow2_prompt.txt',
            'repair_arrow3': 'repair_arrow3_prompt.txt',
            'nl2smt': 'roundtrip_promptNL2SMT.txt',
            'smt2nl': 'roundtrip_promptSMT2NL.txt'
        }

        for name, filename in template_files.items():
            template_path = self.prompts_dir / filename
            if template_path.exists():
                with open(template_path, 'r') as f:
                    self.templates[name] = f.read()
            else:
                raise FileNotFoundError(f"Template not found: {template_path}")
    
    def diagnose(self, original_nl: str, phase1_smt: str, reconstructed_nl: str, 
                 phase3_smt: str, counterexample: Optional[str] = None) -> Dict[str, any]:
        """
        Diagnose which arrow first failed in the pipeline.
        
        Args:
            original_nl: Original natural language rule
            phase1_smt: Phase 1 SMT encoding
            reconstructed_nl: Reconstructed natural language
            phase3_smt: Phase 3 SMT encoding
            counterexample: Optional Z3 counterexample showing where formulas differ
            
        Returns:
            Dictionary with:
                'first_failed_arrow': int (1, 2, or 3)
                'reasoning': str (diagnostic feedback for repair)
                'raw_response': str (full LLM response)
        """
        # Format counterexample section
        counterexample_text = ""
        if counterexample:
            counterexample_text = counterexample
        else:
            counterexample_text = "Not available"
        
        # Create diagnosis prompt
        prompt = self.templates['diagnosis'].format(
            original_nl=original_nl,
            phase1_smt=phase1_smt,
            reconstructed_nl=reconstructed_nl,
            phase3_smt=phase3_smt,
            counterexample=counterexample_text
        )
        
        # Call diagnosis LLM (which may be different from the repair LLM in cross-model runs)
        response = self.diagnosis_llm_client.generate_with_prompt(prompt, temperature=0.3)
        self.llm_call_counter += 1
        time.sleep(self.request_delay)

        # Parse response
        parsed = self._parse_diagnosis_response(response)
        print(f"    [DEBUG] Parsed diagnosis: Arrow {parsed.get('first_failed_arrow')}, Reasoning length: {len(parsed.get('reasoning', ''))}")
        return parsed
    
    def _parse_diagnosis_response(self, response: str) -> Dict[str, any]:
        """
        Parse diagnosis response to extract failed arrow and reasoning.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Dictionary with 'first_failed_arrow', 'reasoning', 'raw_response'
        """
        lines = response.strip().split('\n')
        
        first_failed_arrow = None
        reasoning = ""
        current_section = None
        
        for line in lines:
            line_stripped = line.strip()
            
            if line_stripped.startswith("FIRST_FAILED_ARROW:"):
                arrow_part = line_stripped.split(":", 1)[1].strip()
                # Extract just the number
                try:
                    first_failed_arrow = int(arrow_part)
                    if first_failed_arrow not in [1, 2, 3]:
                        first_failed_arrow = None
                except:
                    # Try to find digit in the text
                    for char in arrow_part:
                        if char in ['1', '2', '3']:
                            first_failed_arrow = int(char)
                            break
            elif line_stripped.startswith("REASONING:"):
                reasoning_part = line_stripped.split(":", 1)[1].strip()
                reasoning = reasoning_part
                current_section = "reasoning"
            elif current_section == "reasoning" and line_stripped:
                reasoning += " " + line_stripped
        
        # Validation
        if first_failed_arrow is None:
            # Default to Arrow 1 if parsing failed
            first_failed_arrow = 1
            if not reasoning:
                reasoning = "Diagnosis parsing failed. Defaulting to Arrow 1."
        
        return {
            'first_failed_arrow': first_failed_arrow,
            'reasoning': reasoning.strip(),
            'raw_response': response
        }
    
    def repair_arrow_1(self, original_nl: str, reasoning: str) -> tuple:
        """
        Repair Arrow 1: Original NL → Phase 1 SMT.
        
        Args:
            original_nl: Original natural language rule
            reasoning: Diagnostic feedback explaining what went wrong
            
        Returns:
            tuple: (prompt, response) where response is repaired Phase 1 SMT encoding
        """
        prompt = self.templates['repair_arrow1'].format(reasoning=reasoning)
        prompt += f"\n\nSCHEMA:\n{self.schema_content}\n\n"
        prompt += f"NATURAL LANGUAGE RULE:\n{original_nl}\n\n"
        prompt += "Provide the corrected SMT-LIB encoding:"
        
        response = self.llm_client.generate_with_prompt(prompt, temperature=0.3)
        self.llm_call_counter += 1
        time.sleep(self.request_delay)
        
        return (prompt, response.strip())
    
    def repair_arrow_2(self, phase1_smt: str, reasoning: str) -> tuple:
        """
        Repair Arrow 2: Phase 1 SMT → Reconstructed NL.
        
        Args:
            phase1_smt: Phase 1 SMT encoding
            reasoning: Diagnostic feedback explaining what went wrong
            
        Returns:
            tuple: (prompt, response) where response is repaired reconstructed natural language
        """
        prompt = self.templates['repair_arrow2'].format(reasoning=reasoning)
        prompt += f"\n\nSCHEMA:\n{self.schema_content}\n\n"
        prompt += f"SMT-LIB FORMULA:\n{phase1_smt}\n\n"
        prompt += "Provide the corrected natural language reconstruction:"
        
        response = self.llm_client.generate_with_prompt(prompt, temperature=0.3)
        self.llm_call_counter += 1
        time.sleep(self.request_delay)
        
        return (prompt, response.strip())
    
    def repair_arrow_3(self, reconstructed_nl: str, reasoning: str) -> tuple:
        """
        Repair Arrow 3: Reconstructed NL → Phase 3 SMT.
        
        Args:
            reconstructed_nl: Reconstructed natural language
            reasoning: Diagnostic feedback explaining what went wrong
            
        Returns:
            tuple: (prompt, response) where response is repaired Phase 3 SMT encoding
        """
        print(f"    [DEBUG] Repair Arrow 3 - Reasoning length: {len(reasoning)}, Reconstructed NL length: {len(reconstructed_nl)}")
        prompt = self.templates['repair_arrow3'].format(reasoning=reasoning)
        prompt += f"\n\nSCHEMA:\n{self.schema_content}\n\n"
        prompt += f"NATURAL LANGUAGE RULE:\n{reconstructed_nl}\n\n"
        prompt += "Provide the corrected SMT-LIB encoding:"
        
        print(f"    [DEBUG] Total prompt length: {len(prompt)} chars")
        response = self.llm_client.generate_with_prompt(prompt, temperature=0.3)
        self.llm_call_counter += 1
        time.sleep(self.request_delay)
        
        return (prompt, response.strip())
    
    def regenerate_arrow_1(self, original_nl: str) -> tuple:
        """
        Re-run Arrow 1 from scratch (Original NL -> Phase 1 SMT) using the
        standard NL2SMT prompt, no repair feedback. Used by --ablation regenerate.

        Args:
            original_nl: Original natural language rule

        Returns:
            tuple: (prompt, response) where response is a fresh Phase 1 SMT encoding
        """
        prompt = self.templates['nl2smt']
        prompt += f"\n\nSCHEMA:\n{self.schema_content}\n\n"
        prompt += f"NATURAL LANGUAGE RULE:\n{original_nl}\n\n"
        prompt += "Provide the SMT-LIB encoding:"

        response = self.llm_client.generate_with_prompt(prompt, temperature=0.3)
        self.llm_call_counter += 1
        time.sleep(self.request_delay)

        return (prompt, response.strip())

    def regenerate_arrow_2(self, phase1_smt: str) -> tuple:
        """
        Re-run Arrow 2 with normal prompt (after Arrow 1 was repaired).
        
        Args:
            phase1_smt: Phase 1 SMT encoding (possibly repaired)
            
        Returns:
            tuple: (prompt, response) where response is reconstructed natural language
        """
        prompt = self.templates['smt2nl']
        prompt += f"\n\nSCHEMA:\n{self.schema_content}\n\n"
        prompt += f"SMT-LIB FORMULA:\n{phase1_smt}\n\n"
        prompt += "Translate to natural language:"
        
        response = self.llm_client.generate_with_prompt(prompt, temperature=0.3)
        self.llm_call_counter += 1
        time.sleep(self.request_delay)
        
        return (prompt, response.strip())
    
    def regenerate_arrow_3(self, reconstructed_nl: str) -> tuple:
        """
        Re-run Arrow 3 with normal prompt (after Arrow 1 or 2 was repaired).
        
        Args:
            reconstructed_nl: Reconstructed natural language (possibly from repaired SMT)
            
        Returns:
            tuple: (prompt, response) where response is Phase 3 SMT encoding
        """
        prompt = self.templates['nl2smt']
        prompt += f"\n\nSCHEMA:\n{self.schema_content}\n\n"
        prompt += f"NATURAL LANGUAGE RULE:\n{reconstructed_nl}\n\n"
        prompt += "Provide the SMT-LIB encoding:"
        
        response = self.llm_client.generate_with_prompt(prompt, temperature=0.3)
        self.llm_call_counter += 1
        time.sleep(self.request_delay)
        
        return (prompt, response.strip())
    
    def run_single_iteration(self, iteration_num, original_nl, phase1_smt, 
                            reconstructed_nl, phase3_smt, counterexample):
        """
        Run a single repair iteration: diagnose, repair, regenerate downstream
        
        Args:
            iteration_num: The iteration number (0, 1, 2, 3)
            original_nl: Original natural language rule
            phase1_smt: Phase 1 SMT encoding (from NL)
            reconstructed_nl: Reconstructed NL (from Phase 1 SMT)
            phase3_smt: Phase 3 SMT encoding (from reconstructed NL)
            counterexample: Counterexample from Z3
            
        Returns:
            dict with:
                'success': bool
                'phase1_smt': Updated phase 1 SMT
                'reconstructed_nl': Updated reconstructed NL
                'phase3_smt': Updated phase 3 SMT
                'diagnosis': Diagnosis dict
                'repaired_arrow': Arrow number that was repaired
                'repair_response': Full LLM response for repair
                'regeneration_responses': Dict of downstream regeneration responses
        """
        print(f"\n[Iteration {iteration_num}] Starting diagnosis... (mode: {self.ablation_mode})")
        
        # Step 1: Determine which arrow to repair (depends on ablation mode)
        if self.ablation_mode == 'regenerate':
            # Full pipeline regeneration. No diagnosis call, no scoped repair.
            # Re-run T1, T2, T3 from original_nl from scratch.
            print(f"[Iteration {iteration_num}] Regenerating full pipeline (T1, T2, T3) from original NL...")
            p1_prompt, phase1_smt = self.regenerate_arrow_1(original_nl)
            p2_prompt, reconstructed_nl = self.regenerate_arrow_2(phase1_smt)
            p3_prompt, phase3_smt = self.regenerate_arrow_3(reconstructed_nl)
            return {
                'success': True,
                'phase1_smt': phase1_smt,
                'reconstructed_nl': reconstructed_nl,
                'phase3_smt': phase3_smt,
                'diagnosis': {
                    'first_failed_arrow': None,
                    'reasoning': 'No diagnosis performed (regenerate ablation: full pipeline rerun).',
                    'raw_response': 'ABLATION: regenerate (no diagnosis call)'
                },
                'repaired_arrow': None,
                'repair_prompt': None,
                'repair_response': None,
                'regeneration_responses': {
                    'arrow_1': phase1_smt,
                    'arrow_2': reconstructed_nl,
                    'arrow_3': phase3_smt,
                },
                'regeneration_prompts': {
                    'arrow_1': p1_prompt,
                    'arrow_2': p2_prompt,
                    'arrow_3': p3_prompt,
                },
            }
        elif self.ablation_mode == 'random':
            # Random arrow selection — no diagnosis LLM call
            import random
            failed_arrow = random.choice([1, 2, 3])
            reasoning = "No diagnosis performed (random arrow ablation)."
            diagnosis = {
                'first_failed_arrow': failed_arrow,
                'reasoning': reasoning,
                'raw_response': 'ABLATION: random arrow selection'
            }
            print(f"[Iteration {iteration_num}] Random arrow selection: Arrow {failed_arrow}")
        else:
            # Full diagnosis (used by both 'full' and 'no_reasoning' modes)
            diagnosis = self.diagnose(original_nl, phase1_smt, reconstructed_nl, 
                                     phase3_smt, counterexample)
            
            if diagnosis['first_failed_arrow'] is None:
                print(f"[Iteration {iteration_num}] ERROR: Could not determine failed arrow")
                return {
                    'success': False,
                    'phase1_smt': phase1_smt,
                    'reconstructed_nl': reconstructed_nl,
                    'phase3_smt': phase3_smt,
                    'diagnosis': diagnosis,
                    'repaired_arrow': None,
                    'repair_response': None,
                    'regeneration_responses': {}
                }
            
            failed_arrow = diagnosis['first_failed_arrow']
            
            if self.ablation_mode == 'no_reasoning':
                # Use diagnosis to pick arrow, but strip reasoning from repair prompt
                reasoning = "A previous attempt had errors. Please re-do this step carefully."
                print(f"[Iteration {iteration_num}] Diagnosis: Arrow {failed_arrow} (reasoning stripped for ablation)")
            else:
                # Full mode — pass reasoning through
                reasoning = diagnosis['reasoning']
        
        print(f"[Iteration {iteration_num}] Diagnosis: Arrow {failed_arrow} failed first")
        print(f"[Iteration {iteration_num}] Reasoning: {reasoning[:100]}...")
        
        # Step 2: Repair the failed arrow
        repair_prompt = None
        repair_response = None
        regeneration_responses = {}
        regeneration_prompts = {}
        
        if failed_arrow == 1:
            # Repair Arrow 1: Original NL → Phase 1 SMT
            print(f"[Iteration {iteration_num}] Repairing Arrow 1 (NL → Phase 1 SMT)...")
            repair_prompt, phase1_smt = self.repair_arrow_1(original_nl, reasoning)
            repair_response = phase1_smt
            
            # Regenerate downstream: Arrow 2 and Arrow 3
            print(f"[Iteration {iteration_num}] Regenerating Arrow 2 (Phase 1 SMT → Reconstructed NL)...")
            regen2_prompt, reconstructed_nl = self.regenerate_arrow_2(phase1_smt)
            regeneration_responses['arrow_2'] = reconstructed_nl
            regeneration_prompts['arrow_2'] = regen2_prompt
            
            print(f"[Iteration {iteration_num}] Regenerating Arrow 3 (Reconstructed NL → Phase 3 SMT)...")
            regen3_prompt, phase3_smt = self.regenerate_arrow_3(reconstructed_nl)
            regeneration_responses['arrow_3'] = phase3_smt
            regeneration_prompts['arrow_3'] = regen3_prompt
            
        elif failed_arrow == 2:
            # Repair Arrow 2: Phase 1 SMT → Reconstructed NL
            print(f"[Iteration {iteration_num}] Repairing Arrow 2 (Phase 1 SMT → Reconstructed NL)...")
            repair_prompt, reconstructed_nl = self.repair_arrow_2(phase1_smt, reasoning)
            repair_response = reconstructed_nl
            
            # Regenerate downstream: Arrow 3
            print(f"[Iteration {iteration_num}] Regenerating Arrow 3 (Reconstructed NL → Phase 3 SMT)...")
            regen3_prompt, phase3_smt = self.regenerate_arrow_3(reconstructed_nl)
            regeneration_responses['arrow_3'] = phase3_smt
            regeneration_prompts['arrow_3'] = regen3_prompt
            
        elif failed_arrow == 3:
            # Repair Arrow 3: Reconstructed NL → Phase 3 SMT
            print(f"[Iteration {iteration_num}] Repairing Arrow 3 (Reconstructed NL → Phase 3 SMT)...")
            repair_prompt, phase3_smt = self.repair_arrow_3(reconstructed_nl, reasoning)
            repair_response = phase3_smt
            # No downstream to regenerate
            
        print(f"[Iteration {iteration_num}] Repair complete")
        
        return {
            'success': True,
            'phase1_smt': phase1_smt,
            'reconstructed_nl': reconstructed_nl,
            'phase3_smt': phase3_smt,
            'diagnosis': diagnosis,
            'repaired_arrow': failed_arrow,
            'repair_prompt': repair_prompt,
            'repair_response': repair_response,
            'regeneration_responses': regeneration_responses,
            'regeneration_prompts': regeneration_prompts
        }
    
    def run_full_repair(self, original_nl, phase1_smt, reconstructed_nl, 
                       phase3_smt, counterexample, z3_checker, schema):
        """
        Run the complete iterative repair process (up to max_iterations)
        
        Args:
            original_nl: Original natural language rule
            phase1_smt: Initial Phase 1 SMT encoding
            reconstructed_nl: Initial reconstructed NL
            phase3_smt: Initial Phase 3 SMT encoding
            counterexample: Initial counterexample from Z3
            z3_checker: Z3Checker instance for equivalence checking
            schema: SMT schema for Z3 checks
            
        Returns:
            dict with:
                'final_phase1_smt': Final phase 1 SMT
                'final_reconstructed_nl': Final reconstructed NL
                'final_phase3_smt': Final phase 3 SMT
                'final_equivalent': bool (whether final encodings are equivalent)
                'iterations': List of iteration results
                'total_iterations': Number of iterations performed
        """
        print(f"\n{'='*60}")
        print(f"Starting repair process (max {self.max_iterations} iterations)")
        print(f"{'='*60}")
        
        # Track current state
        current_phase1 = phase1_smt
        current_reconstructed = reconstructed_nl
        current_phase3 = phase3_smt
        current_counterexample = counterexample
        
        iterations = []
        
        for iteration_num in range(1, self.max_iterations + 1):
            print(f"\n{'='*60}")
            print(f"ITERATION {iteration_num}/{self.max_iterations}")
            print(f"{'='*60}")
            
            # Run single iteration
            result = self.run_single_iteration(
                iteration_num,
                original_nl,
                current_phase1,
                current_reconstructed,
                current_phase3,
                current_counterexample
            )
            
            if not result['success']:
                print(f"[Iteration {iteration_num}] Failed to diagnose/repair. Stopping.")
                iterations.append(result)
                break
            
            # Update current state with repaired outputs
            current_phase1 = result['phase1_smt']
            current_reconstructed = result['reconstructed_nl']
            current_phase3 = result['phase3_smt']
            
            iterations.append(result)
            
            # Check if encodings are now equivalent
            print(f"[Iteration {iteration_num}] Checking equivalence with Z3...")
            z3_result = z3_checker.check_equivalence_with_schema(current_phase1, current_phase3, schema)
            
            if z3_result['result'] == 'UNSAT':
                print(f"[Iteration {iteration_num}] SUCCESS! Encodings are now equivalent (UNSAT)")
                return {
                    'final_phase1_smt': current_phase1,
                    'final_reconstructed_nl': current_reconstructed,
                    'final_phase3_smt': current_phase3,
                    'final_equivalent': True,
                    'iterations': iterations,
                    'total_iterations': iteration_num
                }
            elif z3_result['result'] == 'SAT':
                print(f"[Iteration {iteration_num}] Still SAT. Counterexample: {z3_result['counterexample']}")
                current_counterexample = z3_result['counterexample']
                # Continue to next iteration
            else:
                print(f"[Iteration {iteration_num}] Z3 returned {z3_result['result']}. Stopping.")
                return {
                    'final_phase1_smt': current_phase1,
                    'final_reconstructed_nl': current_reconstructed,
                    'final_phase3_smt': current_phase3,
                    'final_equivalent': False,
                    'iterations': iterations,
                    'total_iterations': iteration_num
                }
        
        # Exhausted all iterations
        print(f"\n{'='*60}")
        print(f"Exhausted all {self.max_iterations} iterations without achieving UNSAT")
        print(f"{'='*60}")
        
        return {
            'final_phase1_smt': current_phase1,
            'final_reconstructed_nl': current_reconstructed,
            'final_phase3_smt': current_phase3,
            'final_equivalent': False,
            'iterations': iterations,
            'total_iterations': self.max_iterations
        }
