(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (= (roadway_kind r) RK_Other))
      false))

Wait, let me reconsider. The rule is about railroad tracks specifically. Let me look at the schema more carefully.

The schema doesn't have a direct "on_railroad_track" predicate, but there is `Crossing` sort for railroad crossings and `approaching_crossing`. However, there's no predicate for being *on* a railroad track directly.

Looking at the schema, I see `RoadPos` has various positions but no railroad track position specifically. However, there is `RP_StreetcarTrack` which represents being on a streetcar track. Railroad tracks at crossings are the relevant context.

The closest encoding uses the stop actions and railroad crossing context. Since the schema has `approaching_crossing` and `dist_to_nearest_rail_sq` for crossings, and `stopped` for vehicles, but no direct "on railroad track" predicate, I'll use the proximity to rail approach - being essentially at zero distance from the rail (on the track).

The most faithful encoding given the schema:

(forall ((v Vehicle) (c Crossing) (t Int))
  (=> (and (approaching_crossing v c t)
           (<= (dist_to_nearest_rail_sq v c t) ft_5_sq))
      (and (not (= (stop_action v t) SA_Stop))
           (not (= (stop_action v t) SA_Stand))
           (not (= (stop_action v t) SA_Park)))))