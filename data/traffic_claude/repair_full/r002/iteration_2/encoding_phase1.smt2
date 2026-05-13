(exists ((v_pass Vehicle) (v_passed Vehicle) (r Roadway) (t Int))
  (and
    (is_ego v_pass)
    (not (= v_pass v_passed))
    (passing v_pass v_passed t)
    (on_roadway v_pass r t)
    (= (roadway_pos v_pass r t) RP_LeftHalf)))