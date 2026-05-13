(forall ((v Vehicle) (a Access) (t Int))
  (=> (or (crossing_sidewalk v t)
          (turning_into v a t))
      (stopped_before_sidewalk v t)))