(forall ((v Vehicle) (t Int))
  (and
    (=> (or (= (stop_action v t) SA_Stand) (= (stop_action v t) SA_Park))
        (and (>= (dist_to_feature v PF_FireStationDriveway t) ft_20)
             (>= (dist_to_feature v PF_FireStationDriveway t) ft_75)))
    (=> (= (stop_action v t) SA_Stand)
        (passengers_all_safe v t))))