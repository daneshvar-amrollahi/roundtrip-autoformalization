(forall ((p Person) (t Int))
  (=> (and (is_legally_blind p t)
           (is_hunting p t))
      (carries_proof_of p DOK_ProofOfBlindness t)))