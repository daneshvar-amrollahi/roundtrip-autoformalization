(forall ((v Vehicle) (t Int))
  (=> (and (is_ego v)
           (or (stop_action v t) (parked v t) (standing_vehicle v t))
           (or (= (stop_action v t) SA_Stand) (= (stop_action v t) SA_Park))
           (not (and (or (= (stop_action v t) SA_Stop) (= (stop_action v t) SA_Stand))
                     (exists ((t2 Int))
                       (and (<= t t2)
                            (not (stopped v t2)))))))
      (not (or
             (and (not (roadway_pos v (let ((r Roadway)) r) t))
                  false)
             false))))

I need to reconsider this carefully. Let me re-examine the schema and the rule.

(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (is_ego v)
           (on_roadway v r t)
           (or (= (stop_action v t) SA_Stand) (= (stop_action v t) SA_Park))
           (not (and (stopped v t)
                     (or (= (stop_action v t) SA_Stop) (= (stop_action v t) SA_Stand)))))
      (and (>= (dist_to_feature v PF_FireStationDriveway t) ft_20)
           (>= (dist_to_feature v PF_FireStationDriveway t) ft_75))))

Let me reconsider once more and provide a clean, correct encoding:

(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (is_ego v)
           (on_roadway v r t)
           (or (= (stop_action v t) SA_Stand) (= (stop_action v t) SA_Park)))
      (or (and (stopped v t)
               (not (parked v t)))
          (>= (dist_to_feature v PF_FireStationDriveway t) ft_75))))

SCHEMA_INSUFFICIENT: The schema lacks a predicate to determine whether a vehicle is on the same side or opposite side of the street relative to a proximity feature (e.g., a fire station driveway entrance). Without such a predicate, it is impossible to distinguish the 20-foot same-side restriction from the 75-foot opposite-side restriction. The schema also lacks a predicate for "momentarily picking up or discharging a passenger" as distinct from general stopping. Below is the best approximation using the 75-foot threshold (the stricter of the two) with an exception for momentary stops (approximated as SA_Stop):

(forall ((v Vehicle) (t Int))
  (=> (and (is_ego v)
           (or (= (stop_action v t) SA_Stand) (= (stop_action v t) SA_Park))
           (< (dist_to_feature v PF_FireStationDriveway t) ft_75)
           (not (and (= (stop_action v t) SA_Stop)
                     (stopped v t))))
      (>= (dist_to_feature v PF_FireStationDriveway t) ft_75)))