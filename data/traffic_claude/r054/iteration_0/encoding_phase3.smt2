(forall ((v Vehicle) (t Int))
  (=> (= (kind v) VK_Motorcycle)
      (not (between_lanes v t))))