(forall ((v Vehicle) (t Int))
  (=> (< (dist_to_feature v PF_FireStationDriveway t) ft_75)
      (and (not (= (stop_action v t) SA_Stand))
           (not (= (stop_action v t) SA_Park)))))