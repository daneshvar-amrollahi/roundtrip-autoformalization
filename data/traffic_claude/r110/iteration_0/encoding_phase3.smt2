(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (is_ego v)
           (approaching_hill_crest v r t))
      (reduced_speed_appropriate v t)))