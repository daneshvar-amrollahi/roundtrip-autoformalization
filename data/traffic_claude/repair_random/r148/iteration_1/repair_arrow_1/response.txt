(forall ((v Vehicle) (t Int))
  (=> (and (is_ego v)
           (or (and (< (dist_to_feature v PF_FireStationDriveway t) ft_20))
               (and (< (dist_to_feature v PF_FireStationDriveway t) ft_75)
                    (roadway_pos v (let ((r Roadway)) r) t)
                    true))
           (not (and (or (= (stop_action v t) SA_Stand)
                         (= (stop_action v t) SA_Park))
                     (stopped v t))))
       true))

SCHEMA_INSUFFICIENT: The schema lacks a predicate to distinguish being on the same side vs. the opposite side of the street relative to a fire station driveway entrance, and lacks a predicate for "momentarily picking up or discharging a passenger" as an exception.

Let me provide the best approximation possible:

(forall ((v Vehicle) (t Int))
  (=> (and (is_ego v)
           (or (< (dist_to_feature v PF_FireStationDriveway t) ft_20)
               (< (dist_to_feature v PF_FireStationDriveway t) ft_75))
           (or (= (stop_action v t) SA_Stand)
               (= (stop_action v t) SA_Park)))
      false))