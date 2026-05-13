(forall ((v Vehicle) (bus Vehicle) (r Roadway) (t Int))
  (=>
    (and (= (roadway_divided r) DK_Divided)
         (on_roadway v r t)
         (on_roadway bus r t)
         (bus_stopped_for_students bus t)
         (same_roadway_as_bus v bus r t)
         (not (on_right_roadway_of_divided v r t)))
    (not (stopped_before_reaching v bus t))))