(forall ((v Vehicle) (t Int))
  (and (not (passenger_interferes_view v t)) (not (driving_mechanism_interfered v t))))