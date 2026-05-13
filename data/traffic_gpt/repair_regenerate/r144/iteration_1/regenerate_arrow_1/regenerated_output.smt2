(forall ((trailer Vehicle) (t Int))
  (=> (and (is_house_trailer trailer)
           (not (is-stopping trailer t)))
      (not (occupant_in_trailer trailer t))))