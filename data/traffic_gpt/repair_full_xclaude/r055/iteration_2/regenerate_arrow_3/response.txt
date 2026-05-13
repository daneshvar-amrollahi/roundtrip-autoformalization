(forall ((v_pass Vehicle) (v_passed Vehicle) (t Int))
  (=> (and (= (kind v_pass) VK_Motorcycle)
           (not (= v_pass v_passed)))
      (not (passing_in_same_lane v_pass v_passed t))))