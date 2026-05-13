(forall ((v Vehicle) (t Int))
  (=> (view_obstructed_by_load v t)
      (<= (velocity v t) 0.0)))