(forall ((v Vehicle) (t Int))
  (=> (and (is_house_trailer v)
           (not (is-stopping v t)))
      (not (occupant_in_trailer v t))))