(forall ((v Vehicle) (c Crossing) (t Int))
  (=> (and (is_ego v)
           (not (sufficient_undercarriage_clearance v c)))
       (not (approaching_crossing v c t))))