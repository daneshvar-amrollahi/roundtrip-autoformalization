(forall ((v_follower Vehicle) (v_ambulance Vehicle) (t Int))
  (=> (and (following_ambulance v_follower v_ambulance t)
           (not (on_official_business v_follower t)))
      (not (< (distance v_follower v_ambulance t) ft_500_sq))))