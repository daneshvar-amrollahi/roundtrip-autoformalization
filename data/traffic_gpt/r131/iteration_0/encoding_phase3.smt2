(forall ((v Vehicle) (t Int))
  (=> (or (passenger_interferes_view v t)
          (driving_mechanism_interfered v t))
      (not (> (velocity v t) 0.0))))