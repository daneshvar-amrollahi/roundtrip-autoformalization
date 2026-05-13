(forall ((v Vehicle) (u Vehicle) (r Roadway) (t Int))
  (=> (and (is_ego v)
           (on_roadway v r t)
           (not (= v u))
           (or (on_roadway u r t)
               (entering_main_lane u t))
           (roadway_kind r RK_Highway)
           (assured_clear_distance v u t))
      (speed_reasonable_and_prudent v r t)))

SCHEMA_INSUFFICIENT: The schema lacks a sort for persons/pedestrians as distinct road users that can be quantified over in the same way as vehicles. The rule refers to "another person or vehicle," but the schema only has a Vehicle sort. Additionally, the schema lacks a predicate to represent whether another entity is "in compliance with law." The predicate `assured_clear_distance` is used as an approximation but does not perfectly capture the concept. I have encoded the best approximation possible using available schema elements.