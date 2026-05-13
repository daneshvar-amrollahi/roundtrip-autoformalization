(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (on_roadway v r t)
      (speed_reasonable_and_prudent v r t)))