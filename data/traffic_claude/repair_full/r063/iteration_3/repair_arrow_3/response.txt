(forall ((v Vehicle) (d TurnDir) (t Int))
  (=> (and (intends_turn v d t)
           (or (= d TD_Left) (= d TD_Right)))
      (signal_continuous_100ft v d t)))