(forall ((v Vehicle) (t Int))
  (=> (and (on_sidewalk_or_trail v t)
           (not (crossing_sidewalk v t)))
      (not (on_sidewalk_or_trail v t))))