(forall ((v Vehicle) (t Int))
  (=> (and (or (= (stop_action v t) SA_Stand)
               (= (stop_action v t) SA_Park))
           (not (= (stop_action v t) SA_Stop)))
      (and
        (=> (< (dist_to_feature v PF_FireStationDriveway t) ft_20)
            false)
        (=> (< (dist_to_feature v PF_FireStationDriveway t) ft_75)
            false))))