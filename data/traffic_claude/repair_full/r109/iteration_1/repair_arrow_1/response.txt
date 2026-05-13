(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (or (approaching_curve v r t)
          (approaching_curve_or_crest v r t))
      (reduced_speed_appropriate v t)))