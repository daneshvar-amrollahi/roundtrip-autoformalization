(forall ((v Vehicle) (t Int))
  (=> (and (is_house_trailer v)
           (not (stopped v t)))
      (not (occupant_in_trailer v t))))