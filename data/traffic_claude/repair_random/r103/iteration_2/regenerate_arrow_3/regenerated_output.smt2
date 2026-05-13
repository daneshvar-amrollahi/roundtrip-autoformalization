(forall ((v Vehicle) (t Int))
  (=> (and (is_ego v)
           (< (dist_to_feature v PF_RailroadCrossing t) ft_50))
      (not (= (stop_action v t) SA_Park))))