(forall ((v Vehicle) (i Intersection) (t Int))
  (=> (and (in_intersection v i t)
           (< (dist_to_feature v PF_Crosswalk t) ft_20)
           (not (momentary_passenger_action v t)))
      (and (not (= (stop_action v t) SA_Stand))
           (not (= (stop_action v t) SA_Park)))))

SCHEMA_INSUFFICIENT: The schema lacks a predicate `momentary_passenger_action` (or equivalent) to represent "momentarily picking up or discharging a passenger." No existing predicate in the schema captures this concept. The encoding above uses `momentary_passenger_action` as the closest representation of the exception, but it is not defined in the provided schema.