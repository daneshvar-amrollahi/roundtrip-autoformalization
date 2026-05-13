(forall ((v_pass Vehicle) (v_passed Vehicle) (r Roadway) (t Int))
  (=> (and (passing v_pass v_passed t)
           (= (passing_side v_pass v_passed t) PS_Right)
           (on_roadway v_pass r t)
           (on_roadway v_passed r t)
           (or (roadway_sufficient_width r)
               (roadway_has_marked_lanes r)))
      (and
        (not
          (forall ((t2 Int))
            (=> (and (<= t t2)
                     (not (completely_passed v_pass v_passed t2))
                     (audible_signal v_pass v_passed t2))
                (= (roadway_pos v_passed r t2) RP_RightHalf))))
        (not
          (forall ((t2 Int))
            (=> (and (<= t t2)
                     (not (completely_passed v_pass v_passed t2)))
                (not (is-accelerating v_passed t2))))))))