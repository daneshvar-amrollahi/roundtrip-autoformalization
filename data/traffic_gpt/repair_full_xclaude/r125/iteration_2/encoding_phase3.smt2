(forall ((v_op Vehicle) (v_fire Vehicle) (t Int))
  (=> (and (following_fire_apparatus v_op v_fire t)
           (not (on_official_business v_op t)))
      (not (< (distance v_op v_fire t) ft_500_sq))))