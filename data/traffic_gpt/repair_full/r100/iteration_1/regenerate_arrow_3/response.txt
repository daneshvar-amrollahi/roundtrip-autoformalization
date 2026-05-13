(forall ((v Vehicle) (t Int))
  (=> (<= (dist_to_feature v PF_FireHydrant t) ft_15)
      (and
        (not (parked v t))
        (=> (standing_vehicle v t) (not (parked v t))))))