(forall ((hunter Person) (t Int))
  (=> (has_physical_disability hunter t)
      (carries_proof_of hunter DOK_ProofOfDisability t)))