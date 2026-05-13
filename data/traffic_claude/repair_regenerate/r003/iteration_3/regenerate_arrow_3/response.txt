(forall ((v_ego Vehicle) (v_other Vehicle) (r Roadway) (i Intersection) (t Int))
  (=> (and (on_roadway v_ego r t)
           (obstruction_present v_ego r t)
           (crossing_center_line v_ego r t)
           (= (roadway_pos v_ego r t) RP_LeftHalf)
           (not (= v_ego v_other))
           (on_roadway v_other r t)
           (not (obstruction_present v_other r t))
           (intersection_on_roadway i r)
           (is_immediate_hazard v_other v_ego i t))
      (yield_right_of_way_to_pedestrian v_ego t)))

Wait - `yield_right_of_way_to_pedestrian` is specifically for pedestrians. Let me reconsider. The schema doesn't have a general `yield_right_of_way` predicate for vehicles. However, the concept of yielding right-of-way in this context means the ego vehicle must not proceed into the intersection when the other vehicle is an immediate hazard - i.e., the intersection cannot be safely entered.

Let me re-encode:

(forall ((v_ego Vehicle) (v_other Vehicle) (r Roadway) (i Intersection) (t Int))
  (=> (and (on_roadway v_ego r t)
           (obstruction_present v_ego r t)
           (crossing_center_line v_ego r t)
           (= (roadway_pos v_ego r t) RP_LeftHalf)
           (not (= v_ego v_other))
           (on_roadway v_other r t)
           (not (obstruction_present v_other r t))
           (intersection_on_roadway i r)
           (is_immediate_hazard v_other v_ego i t))
      (not (entering_intersection v_ego i t))))