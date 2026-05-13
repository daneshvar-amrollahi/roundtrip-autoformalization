(forall ((v Vehicle) (t Int))
  (=> (is_ego v)
      (and (not (passenger_interferes_view v t))
           (not (driving_mechanism_interfered v t)))))