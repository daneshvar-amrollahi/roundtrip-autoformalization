(forall ((v Vehicle) (z Zone) (t Int))
  (=> (is_safety_zone z)
      (and
        (=> (in_zone v z t)
            (and
              (not (= (stop_action v t) SA_Stop))
              (not (= (stop_action v t) SA_Stand))
              (not (= (stop_action v t) SA_Park))))
        (=> (< (dist_to_feature v PF_SafetyZone t) ft_30)
            (and
              (not (= (stop_action v t) SA_Stop))
              (not (= (stop_action v t) SA_Stand))
              (not (= (stop_action v t) SA_Park)))))))