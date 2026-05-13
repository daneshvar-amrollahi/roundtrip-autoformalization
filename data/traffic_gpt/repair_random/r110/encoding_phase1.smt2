(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (approaching_hill_crest v r t))
      (reduced_speed_appropriate v t)))