(forall ((v Vehicle) (t Int))
  (=> (or
        (exists ((i Intersection))
          (or (approaching_intersection v i t)
              (in_intersection v i t)))
        (exists ((c Crossing))
          (or (approaching_crossing v c t)
              (permitted_to_proceed v c t))))
      (reduced_speed_appropriate v t)))