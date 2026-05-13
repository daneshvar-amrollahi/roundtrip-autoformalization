"""
NL Comparator - Semantic similarity between original and reconstructed natural language.

Uses bidirectional MNLI entailment with principled categorization.

Key insight: True semantic equivalence requires MUTUAL entailment:
  - Original → Reconstructed (forward: E1)
  - Reconstructed → Original (backward: E2)

Two independent signals:
  - E_min = min(E1, E2): Both must entail for equivalence
  - C_max = max(C1, C2): Any contradiction is concerning

Categories (based on BOTH E_min AND C_max, plus asymmetry):
  - CONTRADICTION: C_max ≥ 0.6 (genuine semantic conflict)
  - EQUIVALENT: E_min ≥ 0.7 and C_max < 0.2 (strong mutual entailment)
  - STRENGTHENED: E1 ≥ 0.6, E2 < 0.4, C_max < 0.3 (reconstruction adds constraints)
  - WEAKENED: E2 ≥ 0.6, E1 < 0.4, C_max < 0.3 (reconstruction drops constraints)
  - RELATED: E_min ≥ 0.3 and C_max < 0.3 (some connection)
  - UNRELATED: E_min < 0.3 and C_max < 0.3 (no clear relationship)

Score = E_min - C_max is still computed for ranking within categories.
"""

import torch

# Thresholds (principled: based on what the probabilities actually mean)
CONTRADICTION_THRESHOLD = 0.6   # High C_max = genuine semantic conflict
EQUIVALENT_E_MIN = 0.7          # Both directions must strongly entail
EQUIVALENT_C_MAX = 0.2          # No significant contradiction
ASYMMETRY_HIGH = 0.6            # One direction entails strongly
ASYMMETRY_LOW = 0.4             # Other direction doesn't
RELATED_E_MIN = 0.3             # Some mutual entailment
RELATED_C_MAX = 0.3             # Low contradiction

# Global model cache
_direct_model = None
_direct_tokenizer = None


def _get_direct_nli_scores(premise: str, hypothesis: str) -> dict:
    """
    Get NLI scores using direct model inference.
    
    Returns dict with keys: 'entailment', 'neutral', 'contradiction'
    """
    global _direct_model, _direct_tokenizer
    
    if _direct_model is None:
        print("Loading NLI model: facebook/bart-large-mnli...")
        print(f"Categorization thresholds:")
        print(f"  CONTRADICTION:  C_max ≥ {CONTRADICTION_THRESHOLD}")
        print(f"  EQUIVALENT:     E_min ≥ {EQUIVALENT_E_MIN} and C_max < {EQUIVALENT_C_MAX}")
        print(f"  STRENGTHENED:   E_forward ≥ {ASYMMETRY_HIGH}, E_backward < {ASYMMETRY_LOW}")
        print(f"  WEAKENED:       E_backward ≥ {ASYMMETRY_HIGH}, E_forward < {ASYMMETRY_LOW}")
        print(f"  RELATED:        E_min ≥ {RELATED_E_MIN}")
        print(f"  UNRELATED:      otherwise")

        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        model_name = "facebook/bart-large-mnli"
        _direct_tokenizer = AutoTokenizer.from_pretrained(model_name)
        _direct_model = AutoModelForSequenceClassification.from_pretrained(model_name)

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device.upper()}")

        if device != "cpu":
            _direct_model = _direct_model.to(device)
        _direct_model.eval()
        print("NLI model loaded successfully.\n")

    # Tokenize
    inputs = _direct_tokenizer(premise, hypothesis, return_tensors="pt", truncation=True, max_length=512)

    # Move to device if needed
    device = next(_direct_model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = _direct_model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)[0].cpu().numpy()

    # BART-MNLI labels: contradiction (0), neutral (1), entailment (2)
    return {
        'contradiction': float(probs[0]),
        'neutral': float(probs[1]),
        'entailment': float(probs[2])
    }


def compute_similarity_score(original: str, reconstructed: str) -> dict:
    """
    Compute semantic similarity between original and reconstructed text.
    
    Uses bidirectional NLI:
      - Forward: original → reconstructed (E1)
      - Backward: reconstructed → original (E2)
    
    Two key signals:
      - E_min = min(E1, E2): Both must entail for equivalence
      - C_max = max(C1, C2): Any contradiction is concerning
    
    Categories based on BOTH signals plus asymmetry:
      - CONTRADICTION: C_max ≥ 0.6
      - EQUIVALENT: E_min ≥ 0.7 and C_max < 0.2
      - STRENGTHENED: E1 high, E2 low (reconstruction more specific)
      - WEAKENED: E2 high, E1 low (reconstruction more general)
      - RELATED: E_min ≥ 0.3, C_max low
      - UNRELATED: neither entails nor contradicts
    
    Returns dict with all probabilities and categorization.
    """
    # Get bidirectional scores
    forward = _get_direct_nli_scores(original, reconstructed)
    backward = _get_direct_nli_scores(reconstructed, original)
    
    E1 = forward['entailment']      # Original entails Reconstructed
    E2 = backward['entailment']     # Reconstructed entails Original
    C1 = forward['contradiction']
    C2 = backward['contradiction']
    
    # Compute key values
    E_min = min(E1, E2)
    C_max = max(C1, C2)
    
    # Score for ranking (still useful within categories)
    score = E_min - C_max
    
    # Categorize based on BOTH E_min and C_max, plus asymmetry
    if C_max >= CONTRADICTION_THRESHOLD:
        category = "CONTRADICTION"
    elif E_min >= EQUIVALENT_E_MIN and C_max < EQUIVALENT_C_MAX:
        category = "EQUIVALENT"
    elif E1 >= ASYMMETRY_HIGH and E2 < ASYMMETRY_LOW and C_max < RELATED_C_MAX:
        category = "STRENGTHENED"  # Reconstruction is more specific/constrained
    elif E2 >= ASYMMETRY_HIGH and E1 < ASYMMETRY_LOW and C_max < RELATED_C_MAX:
        category = "WEAKENED"      # Reconstruction is more general/permissive
    elif E_min >= RELATED_E_MIN and C_max < RELATED_C_MAX:
        category = "RELATED"
    else:
        category = "UNRELATED"
    
    return {
        'score': score,
        'category': category,
        'E_min': E_min,
        'C_max': C_max,
        'E1': E1,  # Forward entailment (orig → recon)
        'E2': E2,  # Backward entailment (recon → orig)
        'forward_entailment': E1,
        'forward_neutral': forward['neutral'],
        'forward_contradiction': C1,
        'backward_entailment': E2,
        'backward_neutral': backward['neutral'],
        'backward_contradiction': C2,
    }


def compare_rules(original_nl: str, reconstructed_nl: str, rule_name: str = None) -> dict:
    """
    Compare original and reconstructed NL for a rule.
    
    This is the main entry point used by nli_analyzer.py.
    
    Returns dict compatible with the analyzer's expectations.
    """
    result = compute_similarity_score(original_nl, reconstructed_nl)
    
    # Map to the format expected by nli_analyzer
    return {
        'rule_name': rule_name,
        'original_nl': original_nl,
        'reconstructed_nl': reconstructed_nl,
        'equivalence': result['category'],  # STRONG/GOOD/WEAK/PROBLEMATIC
        'score': result['score'],
        'E_min': result['E_min'],
        'C_max': result['C_max'],
        'forward_entailment': result['forward_entailment'],
        'forward_neutral': result['forward_neutral'],
        'forward_contradiction': result['forward_contradiction'],
        'backward_entailment': result['backward_entailment'],
        'backward_neutral': result['backward_neutral'],
        'backward_contradiction': result['backward_contradiction'],
        'rationale': _generate_rationale(result)
    }


def _generate_rationale(result: dict) -> str:
    """Generate human-readable explanation of the categorization."""
    E_min = result['E_min']
    C_max = result['C_max']
    E1 = result.get('E1', result.get('forward_entailment', 0))
    E2 = result.get('E2', result.get('backward_entailment', 0))
    category = result['category']
    
    parts = []
    
    # Main category explanation
    if category == "CONTRADICTION":
        parts.append(f"High contradiction (C_max={C_max:.2f} ≥ {CONTRADICTION_THRESHOLD})")
    elif category == "EQUIVALENT":
        parts.append(f"Strong mutual entailment (E_min={E_min:.2f}), low contradiction (C_max={C_max:.2f})")
    elif category == "STRENGTHENED":
        parts.append(f"Orig→Recon strong ({E1:.2f}), Recon→Orig weak ({E2:.2f}): reconstruction adds constraints")
    elif category == "WEAKENED":
        parts.append(f"Recon→Orig strong ({E2:.2f}), Orig→Recon weak ({E1:.2f}): reconstruction drops constraints")
    elif category == "RELATED":
        parts.append(f"Some mutual entailment (E_min={E_min:.2f}), low contradiction")
    else:  # UNRELATED
        parts.append(f"Low mutual entailment (E_min={E_min:.2f}), no clear relationship")
    
    # Add asymmetry note if significant
    if abs(E1 - E2) > 0.3 and category not in ["STRENGTHENED", "WEAKENED"]:
        if E1 > E2:
            parts.append(f"asymmetric: forward stronger ({E1:.2f} vs {E2:.2f})")
        else:
            parts.append(f"asymmetric: backward stronger ({E2:.2f} vs {E1:.2f})")
    
    return "; ".join(parts)


def run_retrieval_test(originals: list, reconstructions: list, rule_names: list = None) -> dict:
    """
    Retrieval test: For each original, can we find its correct reconstruction?
    
    This catches pairing bugs and validates that the similarity metric works.
    
    Args:
        originals: List of original NL texts
        reconstructions: List of reconstructed NL texts (same order as originals)
        rule_names: Optional list of rule names
    
    Returns:
        dict with:
        - top1_accuracy: % of rules where correct pair ranked #1
        - results: detailed per-rule results
        - margins: score difference between correct pair and best wrong pair
    """
    n = len(originals)
    assert len(reconstructions) == n, "Must have same number of originals and reconstructions"
    
    if rule_names is None:
        rule_names = [f"rule_{i}" for i in range(n)]
    
    # Precompute all pairwise scores (n x n matrix)
    print(f"Computing {n}x{n} = {n*n} pairwise similarity scores...")
    scores = []
    for i in range(n):
        row = []
        for j in range(n):
            result = compute_similarity_score(originals[i], reconstructions[j])
            row.append(result['score'])
        scores.append(row)
        print(f"  [{i+1}/{n}] {rule_names[i]} done")
    
    # Evaluate retrieval
    correct_count = 0
    margins = []
    results = []
    
    for i in range(n):
        correct_score = scores[i][i]  # Score with true pair
        
        # Find best wrong score
        wrong_scores = [scores[i][j] for j in range(n) if j != i]
        best_wrong = max(wrong_scores) if wrong_scores else -1
        best_wrong_idx = [j for j in range(n) if j != i and scores[i][j] == best_wrong][0]
        
        margin = correct_score - best_wrong
        margins.append(margin)
        
        # Check if correct pair ranked #1
        is_correct = correct_score >= best_wrong
        if is_correct:
            correct_count += 1
        
        results.append({
            'rule': rule_names[i],
            'correct_score': correct_score,
            'best_wrong_score': best_wrong,
            'best_wrong_rule': rule_names[best_wrong_idx],
            'margin': margin,
            'ranked_first': is_correct
        })
    
    top1_accuracy = correct_count / n
    
    return {
        'top1_accuracy': top1_accuracy,
        'correct_count': correct_count,
        'total': n,
        'median_margin': sorted(margins)[n // 2],
        'min_margin': min(margins),
        'negative_margin_count': sum(1 for m in margins if m < 0),
        'results': results
    }


def run_identity_sanity_check(texts: list, names: list = None) -> dict:
    """
    Sanity check: Compare each text to itself.
    
    Identity pairs should get near-perfect scores (close to 1.0).
    If they don't, something is wrong with the test setup.
    
    Returns:
        dict with scores and pass/fail status
    """
    if names is None:
        names = [f"text_{i}" for i in range(len(texts))]
    
    print(f"Running identity sanity check on {len(texts)} texts...")
    
    results = []
    for i, text in enumerate(texts):
        result = compute_similarity_score(text, text)
        results.append({
            'name': names[i],
            'score': result['score'],
            'E_min': result['E_min'],
            'C_max': result['C_max']
        })
        print(f"  [{i+1}/{len(texts)}] {names[i]}: score={result['score']:.3f}")
    
    scores = [r['score'] for r in results]
    min_score = min(scores)
    median_score = sorted(scores)[len(scores) // 2]
    
    # Identity should have very high scores
    passed = min_score >= 0.8
    
    return {
        'passed': passed,
        'min_score': min_score,
        'median_score': median_score,
        'results': results,
        'message': "PASS: Identity check passed" if passed else f"FAIL: Minimum identity score {min_score:.3f} < 0.8"
    }
