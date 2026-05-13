(forall ((v_operator Vehicle) (v_police Vehicle) (t Int))
  (=> (and (police_signal_given v_police v_operator t)
           (fleeing_police v_operator t))
      (directed_by_police v_operator t)))