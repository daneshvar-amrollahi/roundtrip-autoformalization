(exists ((v_pass Vehicle) (v_passed Vehicle) (r Roadway) (t Int))
  (and
    (not (= v_pass v_passed))
    (on_roadway v_pass r t)
    (on_roadway v_passed r t)
    (passing v_pass v_passed t)
    (crossing_center_line v_pass r t)))