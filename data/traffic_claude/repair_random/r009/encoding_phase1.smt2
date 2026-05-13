(forall ((v_pass Vehicle) (v_passed Vehicle) (t Int))
  (=> (passing v_pass v_passed t)
      (and (= (passing_side v_pass v_passed t) PS_Left)
           (safe-distance v_pass v_passed t))))