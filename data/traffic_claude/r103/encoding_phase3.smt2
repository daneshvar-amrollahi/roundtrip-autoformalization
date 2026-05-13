(forall ((v Vehicle) (t Int))
  (=> (parked v t)
      (>= (dist_to_feature v PF_RailroadCrossing t) ft_50)))