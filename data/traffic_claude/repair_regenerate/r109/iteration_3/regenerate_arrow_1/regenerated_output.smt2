(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (is_ego v)
           (approaching_curve v r t))
      (reduced_speed_appropriate v t)))