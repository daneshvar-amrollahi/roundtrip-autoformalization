(forall ((v_follow Vehicle) (v_fire Vehicle) (t Int))
  (=> (and (following_fire_apparatus v_follow v_fire t)
           (not (on_official_business v_follow t)))
      (<= ft_500_sq (distance v_follow v_fire t))))