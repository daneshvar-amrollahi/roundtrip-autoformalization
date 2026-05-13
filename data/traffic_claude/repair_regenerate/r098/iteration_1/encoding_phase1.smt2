(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (= (roadway_kind r) RK_Other))
      (and (not (= (stop_action v t) SA_Stop))
           (not (= (stop_action v t) SA_Stand))
           (not (= (stop_action v t) SA_Park)))))

SCHEMA_INSUFFICIENT: The schema lacks a predicate to represent that a vehicle is on a railroad track. There is no `on_railroad_track(Vehicle, Int)` or similar predicate. The closest approximation uses railroad crossing predicates, but those represent approaching a crossing, not being physically on a track. The `RoadPos` datatype includes `RP_StreetcarTrack` but not a railroad track position. Below is the best approximation using `RP_StreetcarTrack` as a proxy for being on a track:

(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (= (roadway_pos v r t) RP_StreetcarTrack))
      (and (not (= (stop_action v t) SA_Stop))
           (not (= (stop_action v t) SA_Stand))
           (not (= (stop_action v t) SA_Park)))))