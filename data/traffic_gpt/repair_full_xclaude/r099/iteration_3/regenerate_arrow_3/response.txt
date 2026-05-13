(forall ((v Vehicle) (t Int))
  (=> (in_front_of_driveway v t)
      (and (not (= (stop_action v t) SA_Stand))
           (not (= (stop_action v t) SA_Park)))))