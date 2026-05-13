(forall ((v Vehicle) (t Int))
  (=> (is_ego v)
      (not (reckless_driving v t))))