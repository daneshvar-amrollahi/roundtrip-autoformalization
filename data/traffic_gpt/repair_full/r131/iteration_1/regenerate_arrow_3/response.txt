(forall ((v Vehicle) (t Int))
  (=> (and (passenger_interferes_view v t)
           (driving_mechanism_interfered v t))
      (reckless_driving v t)))