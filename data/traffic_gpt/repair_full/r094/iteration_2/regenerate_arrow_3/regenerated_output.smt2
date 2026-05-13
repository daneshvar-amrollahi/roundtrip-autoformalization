(forall ((v Vehicle) (t Int))
  (=> (and (stopped v t)
           (on_sidewalk_or_trail v t))
      (not (= (stop_action v t) SA_Stop))))