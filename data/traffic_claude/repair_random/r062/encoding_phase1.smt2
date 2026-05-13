(forall ((v Vehicle) (t Int))
  (=> (is_ego v)
      (and
        (=> (exists ((td TurnDir)) (intends_turn v td t))
            (exists ((td TurnDir)) (and (intends_turn v td t) (turn_signal_on v td t))))
        (=> (exists ((td TurnDir)) (intends_lane_change v td t))
            (exists ((td TurnDir)) (and (intends_lane_change v td t) (turn_signal_on v td t))))
        (=> (and (parked v t) (not (parked v (+ t 1))))
            (or (turn_signal_on v TD_Left t) (turn_signal_on v TD_Right t))))))