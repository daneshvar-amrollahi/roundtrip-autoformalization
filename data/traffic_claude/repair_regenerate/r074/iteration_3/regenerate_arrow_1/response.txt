(forall ((v_entering Vehicle) (v_approaching Vehicle) (a Access) (r Roadway) (t Int))
  (=> (and (not (= v_entering v_approaching))
           (or (emerging_from v_entering a t)
               (turning_into v_entering a t))
           (access_on_roadway a r)
           (or (= (access_kind a) AK_Alley)
               (= (access_kind a) AK_Building)
               (= (access_kind a) AK_PrivateRoad)
               (= (access_kind a) AK_Driveway))
           (on_roadway v_approaching r t))
      (yield_right_of_way_to_pedestrian v_entering t)))

I need to reconsider - `yield_right_of_way_to_pedestrian` is for pedestrians, not vehicles. Let me look at the schema more carefully for yielding to vehicles.

The schema doesn't have a direct `yield_right_of_way_to_vehicle` predicate, but the semantic meaning of yielding right-of-way to an approaching vehicle means the entering vehicle must not enter/cross in a way that creates an immediate hazard - essentially the entering vehicle must ensure assured clear distance and that the approaching vehicle is not an immediate hazard. Let me use the available predicates to capture this:

(forall ((v_entering Vehicle) (v_approaching Vehicle) (a Access) (r Roadway) (t Int))
  (=> (and (not (= v_entering v_approaching))
           (emerging_from v_entering a t)
           (access_on_roadway a r)
           (or (= (access_kind a) AK_Alley)
               (= (access_kind a) AK_Building)
               (= (access_kind a) AK_PrivateRoad)
               (= (access_kind a) AK_Driveway))
           (on_roadway v_approaching r t))
      (and (not (entering_main_lane v_entering t))
           (sufficient_space_for_vehicle_to_enter v_entering v_approaching t)
           (assured_clear_distance v_entering v_approaching t))))

Hmm, but this blocks entering entirely. Yielding means: don't proceed unless it's safe. Let me reconsider:

(forall ((v_entering Vehicle) (v_approaching Vehicle) (a Access) (r Roadway) (t Int))
  (=> (and (not (= v_entering v_approaching))
           (emerging_from v_entering a t)
           (access_on_roadway a r)
           (or (= (access_kind a) AK_Alley)
               (= (access_kind a) AK_Building)
               (= (access_kind a) AK_PrivateRoad)
               (= (access_kind a) AK_Driveway))
           (on_roadway v_approaching r t)
           (not (sufficient_space_for_vehicle_to_enter v_entering v_approaching t)))
      (not (entering_main_lane v_entering t))))