(forall ((v Vehicle) (d TurnDir) (t Int))
  (=> (intends_lane_change v d t)
      (movement_can_be_made_safely v t)))