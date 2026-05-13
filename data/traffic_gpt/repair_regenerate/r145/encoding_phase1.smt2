(forall ((v_draw Vehicle) (t Int))
  (=> (drawing_another_vehicle v_draw t)
      (<= (drawbar_length v_draw t) ft_15)))