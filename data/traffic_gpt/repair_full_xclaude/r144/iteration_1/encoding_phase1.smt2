(forall ((tr Vehicle) (t Int))
  (=> (and (is_house_trailer tr)
           (> (velocity tr t) 0.0))
      (not (occupant_in_trailer tr t))))