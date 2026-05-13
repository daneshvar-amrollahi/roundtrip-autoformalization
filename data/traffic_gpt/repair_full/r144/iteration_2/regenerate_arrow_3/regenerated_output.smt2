(forall ((trailer Vehicle) (t Int))
  (=> (and (is_house_trailer trailer)
           (not (stopped trailer t)))
      (not (occupant_in_trailer trailer t))))