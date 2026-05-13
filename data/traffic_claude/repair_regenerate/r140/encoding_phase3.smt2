(forall ((v_passed Vehicle) (v_passer Vehicle) (t Int))
  (=> (and (passing v_passer v_passed t)
           (= (passing_side v_passer v_passed t) PS_Right))
      (and
        (=> (audible_signal v_passer v_passed t)
            (close_to_right_edge_practicable v_passed
              (lane_on_roadway (ite true
                (let ((r_dummy Roadway)) r_dummy)
                (let ((r_dummy Roadway)) r_dummy)))
              t))
        (not (is-accelerating v_passed t)))))

Wait, I need to reconsider - I can't use `close_to_right_edge_practicable` with a fabricated roadway. Let me use proper quantification.

(forall ((v_passed Vehicle) (v_passer Vehicle) (r Roadway) (t Int))
  (=> (and (passing v_passer v_passed t)
           (= (passing_side v_passer v_passed t) PS_Right)
           (on_roadway v_passed r t))
      (and
        (=> (audible_signal v_passer v_passed t)
            (close_to_right_edge_practicable v_passed r t))
        (not (is-accelerating v_passed t)))))