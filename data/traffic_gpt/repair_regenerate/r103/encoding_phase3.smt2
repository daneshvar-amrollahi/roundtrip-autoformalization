(forall ((v Vehicle) (c Crossing) (t Int))
  (=> (and (<= (dist_to_nearest_rail_sq v c t) ft_50_sq)
           (not (= (stop_action v t) SA_Stand)))
      (not (parked v t))))