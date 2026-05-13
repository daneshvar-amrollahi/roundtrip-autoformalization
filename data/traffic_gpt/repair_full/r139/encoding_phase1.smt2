(forall ((v Vehicle) (c Crossing) (t Int))
  (=> (and (approaching_crossing v c t)
           (not (sufficient_undercarriage_clearance v c)))
      (not (permitted_to_proceed v c t))))