(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (approaching_curve v r t))
      (reduced_speed_appropriate v t)))