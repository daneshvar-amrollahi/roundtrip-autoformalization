(exists ((v_passed Vehicle) (r Roadway) (t Int))
  (and
    (not (= v_passed (as ego Vehicle)))
    (is_ego (as ego Vehicle))
    (passing (as ego Vehicle) v_passed t)
    (on_roadway (as ego Vehicle) r t)
    (= (roadway_pos (as ego Vehicle) r t) RP_LeftHalf)))

Wait, I need to reconsider. The schema doesn't define a constant `ego`. Let me re-encode properly using quantification over vehicles.

(exists ((v_ego Vehicle) (v_passed Vehicle) (r Roadway) (t Int))
  (and
    (is_ego v_ego)
    (not (= v_ego v_passed))
    (passing v_ego v_passed t)
    (on_roadway v_ego r t)
    (= (roadway_pos v_ego r t) RP_LeftHalf)))