(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (roadway_is_narrow_or_winding r))
      (reduced_speed_appropriate v t)))