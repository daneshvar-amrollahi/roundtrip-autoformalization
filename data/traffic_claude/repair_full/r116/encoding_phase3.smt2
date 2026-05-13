(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (= (roadway_kind r) RK_Beach))
      (<= (velocity v t) mph_15)))