"""
Roundtrip mode: NL → SMT → NL → SMT with schema awareness
"""

from pathlib import Path
from ..llm_client import LLMClient
from ..file_handler import FileHandler
from ..roundtrip_processor import RoundtripProcessor


def run_roundtrip_mode(domain_dir: Path, rules_dir: Path, output_dir: Path, api_key: str,
                      model: str, temperature: float, top_p: float, max_repair_attempts: int,
                      request_delay: float, provider: str = "openai"):
    """
    Run roundtrip mode: NL → SMT with schema awareness.

    This mode allows the LLM to flag if the schema is insufficient to encode a rule,
    rather than generating an incorrect or incomplete formula.

    Args:
        domain_dir: Path to domain config directory (contains schema.smt2 and prompts/)
        rules_dir: Path to rules directory
        output_dir: Path to output directory
        api_key: API key (OpenAI or Anthropic)
        model: Model name to use
        temperature: Sampling temperature
        top_p: Nucleus sampling parameter
        max_repair_attempts: Maximum attempts to repair malformed encodings
        request_delay: Delay in seconds between API requests
        provider: LLM provider - 'openai' or 'anthropic' (default: 'openai')
    """
    print("Running in ROUNDTRIP mode: NL → SMT with schema awareness")
    print(f"Domain: {domain_dir.name}")
    print(f"Schema: {domain_dir / 'schema.smt2'}")
    print(f"Prompts: {domain_dir / 'prompts'}")
    print(f"Rules:   {rules_dir}")
    print(f"Provider: {provider}")
    print(f"Using model: {model}")
    print(f"Temperature: {temperature}, Top-p: {top_p}")
    print(f"Max repair attempts: {max_repair_attempts}")
    print(f"Request delay: {request_delay}s\n")

    # Initialize components
    llm_client = LLMClient(api_key=api_key, model=model, temperature=temperature, top_p=top_p, provider=provider)
    file_handler = FileHandler(
        rules_dir=str(rules_dir),
        domain_dir=str(domain_dir),
        output_dir=str(output_dir)
    )
    processor = RoundtripProcessor(
        llm_client=llm_client,
        file_handler=file_handler,
        max_repair_attempts=max_repair_attempts,
        request_delay=request_delay
    )
    
    # Process all rules
    run_dir = processor.process_all_rules(prompt_file='roundtrip_promptNL2SMT.txt')
    
    print("\n" + "=" * 60)
    print("Roundtrip Complete: NL → SMT → NL → SMT")
    print("=" * 60)
    print(f"\nResults saved to: {run_dir}")
    print("\nOutput files per rule:")
    print("  - original_nl.txt: Original natural language rule")
    print("  - encoding_phase1.smt2: SMT from original NL")
    print("  - reconstructed_nl.txt: NL reconstructed from Phase 1 SMT")
    print("  - encoding_phase3.smt2: SMT from reconstructed NL")
    print("  - schema_issue_phase1.txt: If schema insufficient in Phase 1")
    print("  - schema_issue_phase3.txt: If schema insufficient in Phase 3")
    print("\nNext step (to be implemented):")
    print("  - Equivalence checking: Compare encoding_phase1.smt2 vs encoding_phase3.smt2")
