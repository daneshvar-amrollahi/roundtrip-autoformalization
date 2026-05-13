(forall ((v Vehicle) (t Int))
  (=> (or (passenger_interferes_view v t)
          (driving_mechanism_interfered v t))
      (reckless_driving v t)))