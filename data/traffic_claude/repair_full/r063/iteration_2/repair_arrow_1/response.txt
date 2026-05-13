(forall ((v Vehicle) (d TurnDir) (t Int))
  (=> (and (or (= d TD_Left) (= d TD_Right))
           (intends_turn v d t))
      (signal_continuous_100ft v d t)))