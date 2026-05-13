(forall ((v Vehicle) (t Int))
  (=> (view_obstructed_by_load v t)
      (not (> (velocity v t) 0.0))))