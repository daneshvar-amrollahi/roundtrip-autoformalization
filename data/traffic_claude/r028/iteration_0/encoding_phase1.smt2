(forall ((v Vehicle) (t Int))
  (=> (not (movement_can_be_made_safely v t))
      (not (exists ((d TurnDir)) (intends_lane_change v d t)))))