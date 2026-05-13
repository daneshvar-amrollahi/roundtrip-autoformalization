(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (= (roadway_flow r) FK_OneWay))
      (= (heading v t) (roadway_direction r))))