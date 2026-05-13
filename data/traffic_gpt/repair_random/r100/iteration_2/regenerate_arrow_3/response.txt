(forall ((v Vehicle) (t Int))
  (=> (or (= (stop_action v t) SA_Stand)
          (= (stop_action v t) SA_Park))
      (not (<= (dist_to_feature v PF_FireHydrant t) ft_15))))