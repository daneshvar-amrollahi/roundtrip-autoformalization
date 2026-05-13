(forall ((p Person) (a Animal) (t Int))
  (=> (and (is_legally_blind p t)
           (hunts p a t))
      (carries_proof_of p DOK_ProofOfBlindness t)))