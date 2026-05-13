(exists ((v_ego Vehicle) (v_other Vehicle) (r Roadway) (t Int))
  (and
    (is_ego v_ego)
    (not (= v_ego v_other))
    (on_roadway v_ego r t)
    (= (roadway_pos v_ego r t) RP_LeftHalf)
    (passing v_ego v_other t)))