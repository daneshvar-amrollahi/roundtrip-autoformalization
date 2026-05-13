(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (= (roadway_kind r) RK_Highway))
      (not (racing v t))))