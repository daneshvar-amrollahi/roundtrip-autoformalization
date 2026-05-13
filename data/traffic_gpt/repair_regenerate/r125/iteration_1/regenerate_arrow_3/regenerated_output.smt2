(forall ((v_follower Vehicle) (v_fire Vehicle) (t Int))
  (=> (and (following_fire_apparatus v_follower v_fire t)
           (not (on_official_business v_follower t)))
      (<= ft_500_sq (distance v_follower v_fire t))))