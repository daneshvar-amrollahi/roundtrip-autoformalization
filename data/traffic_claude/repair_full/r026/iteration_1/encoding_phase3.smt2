(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (= (roadway_kind r) RK_Rotary))
      (= (roadway_pos v r t) RP_RightHalf)))