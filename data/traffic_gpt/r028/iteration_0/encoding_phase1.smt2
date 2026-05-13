(forall ((v Vehicle) (t Int))
  (=> (not (movement_can_be_made_safely v t))
      (not (intends_lane_change v TD_Left t))))