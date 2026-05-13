(forall ((v Vehicle) (t Int))
  (=> (and (passenger_interferes_view v t)
           (driving_mechanism_interfered v t))
      (<= (velocity v t) 0.0)))