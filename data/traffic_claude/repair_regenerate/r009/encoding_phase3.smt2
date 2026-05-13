(forall ((v_passer Vehicle) (v_passed Vehicle) (t Int))
  (=> (passing v_passer v_passed t)
      (and (= (passing_side v_passer v_passed t) PS_Left)
           (safe-distance v_passer v_passed t))))