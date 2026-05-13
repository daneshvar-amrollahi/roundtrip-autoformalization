(forall ((v Vehicle) (z Zone) (t Int))
  (=> (is_safety_zone z)
      (and (not (driving_through_safety_zone v z t))
           (not (in_zone v z t)))))