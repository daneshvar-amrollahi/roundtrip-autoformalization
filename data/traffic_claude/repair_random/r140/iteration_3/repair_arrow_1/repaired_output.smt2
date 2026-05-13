(forall ((v_passed Vehicle) (v_passer Vehicle) (t Int))
  (=> (and (passing v_passer v_passed t)
           (= (passing_side v_passer v_passed t) PS_Right))
      (and
        (not (forall ((t2 Int))
               (=> (and (<= t t2)
                        (not (completely_passed v_passer v_passed t2)))
                   (not (is-accelerating v_passed t2)))))
        true)))