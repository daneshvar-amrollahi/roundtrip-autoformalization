(forall ((m Vehicle) (v_other Vehicle) (t Int))
  (=> (and (= (kind m) VK_Motorcycle)
           (not (= m v_other)))
      (not (passing_in_same_lane m v_other t))))