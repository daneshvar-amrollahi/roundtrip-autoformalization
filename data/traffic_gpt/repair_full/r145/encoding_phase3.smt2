(forall ((v Vehicle) (t Int))
  (=> (drawing_another_vehicle v t)
      (<= (drawbar_length v t) ft_15)))