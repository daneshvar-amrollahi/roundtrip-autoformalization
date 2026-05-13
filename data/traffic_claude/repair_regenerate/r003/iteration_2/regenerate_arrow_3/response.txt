(forall ((v_ego Vehicle) (v_other Vehicle) (r Roadway) (i Intersection) (t Int))
  (=> (and (not (= v_ego v_other))
           (on_roadway v_ego r t)
           (on_roadway v_other r t)
           (obstruction_present v_ego r t)
           (crossing_center_line v_ego r t)
           (roadway_free_of_obstructions r t)
           (intersection_on_roadway i r)
           (is_immediate_hazard v_other v_ego i t))
      (yield_right_of_way_to_pedestrian v_ego t)))

Wait — `yield_right_of_way_to_pedestrian` is specifically for pedestrians. Let me reconsider. The schema doesn't have a general `yield_right_of_way` predicate for vehicles. However, the rule says "must yield the right-of-way," and the closest available predicate involves yielding. Let me look more carefully at the schema for intersection-related yielding.

The schema has `is_immediate_hazard`, `intersection_can_be_safely_entered`, and movement predicates. The concept of "yielding right-of-way" to another vehicle can be encoded as: the ego vehicle must not enter the intersection (i.e., must stop/wait) while the other vehicle is an immediate hazard.

Let me re-encode:

(forall ((v_ego Vehicle) (v_other Vehicle) (r Roadway) (i Intersection) (t Int))
  (=> (and (not (= v_ego v_other))
           (on_roadway v_ego r t)
           (on_roadway v_other r t)
           (obstruction_present v_ego r t)
           (crossing_center_line v_ego r t)
           (roadway_free_of_obstructions r t)
           (intersection_on_roadway i r)
           (is_immediate_hazard v_other v_ego i t))
      (not (entering_intersection v_ego i t))))