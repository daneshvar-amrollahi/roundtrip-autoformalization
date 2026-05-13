(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (on_roadway v r t)
      (and
        (speed_reasonable_and_prudent v r t)
        (forall ((u Vehicle))
          (=> (and (not (= v u))
                   (on_roadway u r t))
              (assured_clear_distance v u t))))))