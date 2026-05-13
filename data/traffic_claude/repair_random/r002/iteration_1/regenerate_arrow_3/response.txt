(exists ((v_pass Vehicle) (v_passed Vehicle) (r Roadway) (t Int))
  (and
    (not (= v_pass v_passed))
    (on_roadway v_pass r t)
    (on_roadway v_passed r t)
    (= (roadway_pos v_pass r t) RP_LeftHalf)
    (passing v_pass v_passed t)))