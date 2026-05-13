(forall ((v Vehicle) (t Int))
  (=> (door_open_traffic_side v t)
      (not (door_open_longer_than_necessary v t))))