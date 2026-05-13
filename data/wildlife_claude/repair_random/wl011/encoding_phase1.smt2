(forall ((p Person) (t Int))
  (=> (and (is_hunting p t)
           (has_physical_disability p t))
      (carries_proof_of p DOK_ProofOfDisability t)))