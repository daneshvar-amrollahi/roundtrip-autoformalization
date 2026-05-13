(forall ((v Vehicle) (t Int))
  (not (and (passenger_interferes_view v t)
            (driving_mechanism_interfered v t))))