(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (approaching_curve_or_crest v r t)
           (not (vehicle_visible_within_500ft v t)))
      (not (executing_turn v TD_UTurn t))))