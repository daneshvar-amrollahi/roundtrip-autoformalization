(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (approaching_curve v r t)
      (reduced_speed_appropriate v t)))