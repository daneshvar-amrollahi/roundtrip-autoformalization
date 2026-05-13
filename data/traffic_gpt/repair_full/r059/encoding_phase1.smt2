(forall ((v Vehicle) (r_from Roadway) (r_to Roadway) (t Int))
  (=> (and (on_roadway v r_from t)
           (executing_turn v TD_Left t)
           (roadway_flow r_from) FK_OneWay
           (roadway_flow r_to) FK_OneWay
           (on_roadway v r_to t))
      (close_to_left_curb v r_to t)))