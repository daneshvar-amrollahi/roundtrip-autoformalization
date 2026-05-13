(forall ((p Person) (a Animal) (t Int))
  (=> (and (or (is_kind a AK_DesertBighornSheep)
               (is_kind a AK_PronghornAntelope)
               (is_kind a AK_MuleDeer)
               (is_kind a AK_WhiteTailedDeer))
           (hunts p a t)
           (or (kills p a t) (wounds p a t))
           (protected_by_code a)
           (not (during_open_season (ite (is_kind a AK_DesertBighornSheep) AK_DesertBighornSheep
                                    (ite (is_kind a AK_PronghornAntelope) AK_PronghornAntelope
                                    (ite (is_kind a AK_MuleDeer) AK_MuleDeer
                                         AK_WhiteTailedDeer))) t)))
      (and (not (and (or (acts_intentionally p t) (acts_knowingly p t))
                     (not (makes_reasonable_effort_to_retrieve p a t))))
           (not (and (or (acts_intentionally p t)
                         (acts_knowingly p t)
                         (acts_recklessly p t)
                         (acts_with_criminal_negligence p t))
                     (not (keeps_in_edible_condition p a t)))))))