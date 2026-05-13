"""
Encoding repair module for fixing malformed SMT formulas.
"""

import subprocess
import re
import time
from pathlib import Path
from typing import Tuple, Optional, List
from ..llm_client import LLMClient


class EncodingRepairer:
    """Repairs malformed SMT encodings by iteratively querying the LLM."""
    
    def __init__(self, llm_client: LLMClient, schema_content: str, max_attempts: int = 5, 
                 log_file: Optional[Path] = None, request_delay: float = 0.5):
        """
        Initialize the repairer.
        
        Args:
            llm_client: LLM client for repair queries
            schema_content: SMT schema content
            max_attempts: Maximum repair attempts before giving up
            log_file: Optional path to log file for detailed repair logs
            request_delay: Delay in seconds between API requests
        """
        self.llm_client = llm_client
        self.schema_content = schema_content
        self.max_attempts = max_attempts
        self.repair_history = {}
        self.log_file = log_file
        self.request_delay = request_delay
    
    def _log(self, message: str):
        """Write a message to both console and log file."""
        print(message)
        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(message + '\n')
    
    def _log_error(self, attempt: int, error: str):
        """Log error with truncation for console, full error to file."""
        # Console: truncated
        truncated = error if len(error) <= 150 else error[:150] + "..."
        print(f"      ⚠ Attempt {attempt} failed:")
        print(f"         Error: {truncated}")
        
        # Log file: full error
        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(f"      ⚠ Attempt {attempt} failed:\n")
                f.write(f"         Error: {error}\n")
    
    def repair_encoding(self, encoding: str, rule_name: str, encoding_num: int, 
                       output_dir: Path) -> Tuple[bool, str, List[str]]:
        """
        Repair an encoding until it's valid or max attempts reached.
        
        Args:
            encoding: Initial encoding to repair
            rule_name: Name of the rule
            encoding_num: Encoding number
            output_dir: Directory to save repair attempts
            
        Returns:
            Tuple of (success, final_encoding, error_messages)
            - success: True if repair succeeded, False if gave up
            - final_encoding: The final (possibly repaired) encoding
            - error_messages: List of error messages encountered
        """
        current_encoding = encoding
        error_messages = []
        attempt = 1
        
        # Create the full benchmark for validation
        full_benchmark = self._create_benchmark(current_encoding)
        
        # Save original attempt (full benchmark with schema)
        self._save_attempt(output_dir, encoding_num, attempt, full_benchmark)
        
        while attempt <= self.max_attempts:
            # Validate encoding
            is_valid, errors, full_benchmark = self._validate_encoding(current_encoding)
            
            if is_valid:
                # Success!
                if attempt == 1:
                    self._log(f"      ✓ Valid on first attempt")
                else:
                    self._log(f"      ✓ Repaired successfully after {attempt - 1} attempt(s)")
                
                # Track repair history
                key = f"{rule_name}/encoding_{encoding_num}"
                self.repair_history[key] = {
                    'attempts': attempt,
                    'success': True,
                    'errors': error_messages
                }
                
                return True, current_encoding, error_messages
            
            # Not valid, log error
            error_messages.append(errors)
            self._log_error(attempt, errors)
            
            if attempt >= self.max_attempts:
                # Gave up
                self._log(f"      ✗ Gave up after {self.max_attempts} attempts")
                key = f"{rule_name}/encoding_{encoding_num}"
                self.repair_history[key] = {
                    'attempts': attempt,
                    'success': False,
                    'errors': error_messages
                }
                return False, current_encoding, error_messages
            
            # Try to repair - pass the FULL benchmark so LLM sees line numbers correctly
            self._log(f"      🔧 Requesting repair (attempt {attempt + 1})...")
            current_encoding = self._request_repair(full_benchmark, errors)
            
            # Save repair attempt (full benchmark)
            attempt += 1
            full_benchmark = self._create_benchmark(current_encoding)
            self._save_attempt(output_dir, encoding_num, attempt, full_benchmark)
        
        return False, current_encoding, error_messages
    
    def _create_benchmark(self, encoding: str) -> str:
        """
        Create a full SMT benchmark with schema and encoding.
        
        Args:
            encoding: The encoding formula
            
        Returns:
            Full benchmark content
        """
        return f"""; Validation benchmark
{self.schema_content}

; Check if encoding is well-formed
(assert {encoding})
(check-sat)
"""
    
    def _validate_encoding(self, encoding: str) -> Tuple[bool, str, str]:
        """
        Validate an encoding by running Z3 on it.
        
        Args:
            encoding: SMT encoding to validate
            
        Returns:
            Tuple of (is_valid, error_message, full_benchmark)
        """
        # Create validation benchmark
        benchmark = self._create_benchmark(encoding)
        
        # Write to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.smt2', delete=False) as f:
            f.write(benchmark)
            temp_path = f.name
        
        try:
            # Run Z3
            result = subprocess.run(
                ['z3', temp_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Extract errors
            errors = self._extract_errors(result.stdout)
            
            if errors:
                return False, errors, benchmark
            else:
                return True, "", benchmark
                
        except subprocess.TimeoutExpired:
            return False, "Z3 timeout", benchmark
        except Exception as e:
            return False, f"Validation error: {str(e)}", benchmark
        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
    
    def _extract_errors(self, z3_output: str) -> str:
        """
        Extract error messages from Z3 output.
        
        Z3 prints errors like: (error "message")
        But still prints sat/unsat at the end.
        
        Args:
            z3_output: Raw Z3 output
            
        Returns:
            Extracted error message or empty string if no errors
        """
        # Find all (error ...) patterns using parenthesis matching
        errors = []
        i = 0
        while i < len(z3_output):
            if z3_output[i:].startswith('(error'):
                # Find matching closing parenthesis
                paren_count = 0
                start = i
                for j in range(i, len(z3_output)):
                    if z3_output[j] == '(':
                        paren_count += 1
                    elif z3_output[j] == ')':
                        paren_count -= 1
                        if paren_count == 0:
                            errors.append(z3_output[start:j+1])
                            i = j + 1
                            break
                else:
                    i += 1
            else:
                i += 1
        
        if errors:
            return ' | '.join(errors)
        else:
            return ""
    
    def _request_repair(self, full_benchmark: str, error_message: str) -> str:
        """
        Request LLM to repair a malformed encoding.
        
        Args:
            full_benchmark: The full SMT file with schema and broken encoding
            error_message: Error message from Z3 with line numbers
            
        Returns:
            Repaired encoding (just the formula, not the full benchmark)
        """
        system_prompt = """You are an expert SMT-LIB formula fixer. 

CRITICAL OUTPUT RULES:
- Output ONLY the fixed encoding formula (the part inside the (assert ...))
- NO markdown code blocks (no ```, no ```smt, nothing)
- NO comments (no ; lines)
- NO explanations
- NO text before or after the formula
- Do NOT include the schema or (assert ...) wrapper
- Just the raw formula

REPAIR RULES:
- Only use functions/predicates from the schema in the file
- Use correct types and arity as shown in schema
- Do NOT invent functions - if it's not in the schema, you CANNOT use it"""

        user_prompt = f"""FIX THE BROKEN ENCODING IN THIS FILE:

FULL SMT FILE (with line numbers matching the error):
{full_benchmark}

Z3 ERROR (line numbers refer to the file above):
{error_message}

The error tells you exactly what's wrong and on which line:
- "unknown constant X" means X is NOT in the schema - remove it or use a different approach
- "Sort mismatch" means wrong parameter types - check the schema
- "invalid function application" means wrong number of arguments - check the schema

Look at the line number in the error, find that line in the file above, and fix the issue.

Output ONLY the corrected encoding formula (the part that goes inside (assert ...)). 
NO markdown. NO comments. NO explanations. NO schema. NO (assert ...). Just the formula."""
        
        repaired = self.llm_client.translate_to_smt(
            nl_rule=user_prompt,
            system_prompt=system_prompt
        )
        
        # Rate limiting
        time.sleep(self.request_delay)
        
        return repaired.strip()
    
    def _save_attempt(self, output_dir: Path, encoding_num: int, attempt: int, full_benchmark: str):
        """
        Save a repair attempt to file.
        
        Args:
            output_dir: Directory to save to
            encoding_num: Encoding number
            attempt: Attempt number
            full_benchmark: Full benchmark content (schema + encoding)
        """
        filename = f"encoding_{encoding_num}_attempt_{attempt}.smt2"
        filepath = output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(full_benchmark)
    
    def get_repair_summary(self) -> str:
        """
        Generate a summary of repair attempts.
        
        Returns:
            Summary string for logging
        """
        if not self.repair_history:
            return ""
        
        failures = {k: v for k, v in self.repair_history.items() if not v['success']}
        
        if not failures:
            return ""
        
        summary = "\nREPAIR FAILURES:\n"
        summary += "-" * 50 + "\n"
        
        for key, info in failures.items():
            summary += f"{key}: Failed after {info['attempts']} attempts\n"
            if info['errors']:
                # Truncate long errors at 150 chars for summary
                last_error = info['errors'][-1]
                if len(last_error) > 150:
                    last_error = last_error[:150] + "..."
                summary += f"  Last error: {last_error}\n"
        
        return summary

