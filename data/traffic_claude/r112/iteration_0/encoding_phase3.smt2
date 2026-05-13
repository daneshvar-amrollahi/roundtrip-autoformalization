(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (special_hazard_exists v r t))
      (reduced_speed_appropriate v t)))