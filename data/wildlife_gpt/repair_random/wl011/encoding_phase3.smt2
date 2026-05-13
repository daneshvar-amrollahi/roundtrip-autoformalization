(forall ((p Person) (t Int))
  (=> (has_physical_disability p t)
      (carries_proof_of p DOK_ProofOfDisability t)))