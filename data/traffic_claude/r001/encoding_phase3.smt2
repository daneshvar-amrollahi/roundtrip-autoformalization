(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (roadway_sufficient_width r))
      (= (roadway_pos v r t) RP_RightHalf)))