(forall ((v Vehicle) (t Int))
  (=> (and (is_house_trailer v)
           (> (velocity v t) 0.0))
      (not (occupant_in_trailer v t))))