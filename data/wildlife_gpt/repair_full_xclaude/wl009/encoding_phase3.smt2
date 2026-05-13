(forall ((hunter Person) (t Int))
  (=> (and (is_hunting hunter t)
           (is_legally_blind hunter t))
      (carries_proof_of hunter DOK_ProofOfBlindness t)))