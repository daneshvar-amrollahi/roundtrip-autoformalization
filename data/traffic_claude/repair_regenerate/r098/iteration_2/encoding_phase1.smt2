(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (= (roadway_kind r) RK_Other))
      (and (not (= (stop_action v t) SA_Stop))
           (not (= (stop_action v t) SA_Stand))
           (not (= (stop_action v t) SA_Park)))))

SCHEMA_INSUFFICIENT: The schema lacks a predicate to represent that a vehicle is on a railroad track. There is no `on_railroad_track(Vehicle, Int)` or similar predicate. The closest approximation would use `RoadPos` value `RP_StreetcarTrack`, which represents streetcar tracks rather than railroad tracks. Let me encode using that as the best available approximation:

(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (= (roadway_pos v r t) RP_StreetcarTrack))
      (and (not (= (stop_action v t) SA_Stop))
           (not (= (stop_action v t) SA_Stand))
           (not (= (stop_action v t) SA_Park)))))