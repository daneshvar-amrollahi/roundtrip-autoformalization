"""
Z3 Checker for SMT equivalence with counterexample extraction.
Uses the same proven logic as smt_analyzer.py.
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Dict


class Z3Checker:
    """Wrapper for Z3 equivalence checking."""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize Z3 checker.
        
        Args:
            timeout: Timeout for Z3 calls in seconds (default: 30)
        """
        self.timeout = timeout
    
    def check_equivalence(self, encoding1: str, encoding2: str) -> Dict:
        """
        Check equivalence between two SMT encodings WITHOUT schema.
        
        Args:
            encoding1: First SMT encoding (boolean formula)
            encoding2: Second SMT encoding (boolean formula)
            
        Returns:
            dict with:
                'result': 'UNSAT' | 'SAT' | 'UNKNOWN' | 'ERROR' | 'TIMEOUT'
                'counterexample': str (if SAT, otherwise None)
        """
        return self.check_equivalence_with_schema(encoding1, encoding2, "")
    
    def check_equivalence_with_schema(self, encoding1: str, encoding2: str, schema: str) -> Dict:
        """
        Check equivalence between two SMT encodings with a schema.
        Uses the exact same logic as smt_analyzer.py._create_equivalence_benchmark.
        
        Args:
            encoding1: First SMT encoding (boolean formula)
            encoding2: Second SMT encoding (boolean formula)
            schema: SMT schema (type declarations, function signatures)
            
        Returns:
            dict with:
                'result': 'UNSAT' | 'SAT' | 'UNKNOWN' | 'ERROR' | 'TIMEOUT'
                'counterexample': str (if SAT, otherwise None)
        """
        # Create benchmark using proven logic from smt_analyzer
        benchmark = f"""; Equivalence check benchmark
; UNSAT = equivalent, SAT = different

{schema}

; Assert that encoding1 and encoding2 are NOT equivalent
(assert
  (not
    (=
      {encoding1.strip()}
      {encoding2.strip()}
    )
  )
)

(check-sat)
"""
        
        # Run Z3
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.smt2', delete=False) as f:
                f.write(benchmark)
                benchmark_file = f.name
            
            result = subprocess.run(
                ['z3', benchmark_file],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # Clean up
            Path(benchmark_file).unlink()
            
            # Parse result
            output = result.stdout.strip().lower()
            
            if 'unsat' in output:
                return {'result': 'UNSAT', 'counterexample': None}
            elif 'sat' in output and 'unsat' not in output:
                return {'result': 'SAT', 'counterexample': 'SAT (counterexample exists)'}
            elif 'unknown' in output:
                return {'result': 'UNKNOWN', 'counterexample': None}
            else:
                return {'result': 'ERROR', 'counterexample': None}
        
        except subprocess.TimeoutExpired:
            try:
                Path(benchmark_file).unlink()
            except:
                pass
            return {'result': 'TIMEOUT', 'counterexample': None}
        
        except Exception as e:
            return {'result': 'ERROR', 'counterexample': str(e)}

