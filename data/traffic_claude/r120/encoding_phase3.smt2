(forall ((v Vehicle) (z Zone) (t Int))
  (=> (and (is_ego v) (is_safety_zone z))
      (not (driving_through_safety_zone v z t))))