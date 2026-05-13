(forall ((v Vehicle) (t Int))
  (=> (door_open_traffic_side v t)
      (door_can_open_safely v t)))