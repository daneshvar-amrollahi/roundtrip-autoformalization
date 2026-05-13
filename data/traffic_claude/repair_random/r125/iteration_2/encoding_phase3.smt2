(forall ((v Vehicle) (fa Vehicle) (t Int))
  (=> (and (not (= v fa))
           (kind fa) ;; fa is a fire apparatus
           (= (kind fa) VK_FireApparatus)
           (emergency_signals_active fa t)
           (following v fa t)
           (not (on_official_business v t)))
      (> (distance v fa t) ft_500_sq)))