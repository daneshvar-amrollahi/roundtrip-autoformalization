(forall ((v_entering Vehicle) (v_approaching Vehicle) (a Access) (r Roadway) (t Int))
  (=> (and (not (= v_entering v_approaching))
           (or (emerging_from v_entering a t)
               (turning_into v_entering a t))
           (access_on_roadway a r)
           (or (= (access_kind a) AK_Alley)
               (= (access_kind a) AK_Building)
               (= (access_kind a) AK_PrivateRoad)
               (= (access_kind a) AK_Driveway))
           (on_roadway v_approaching r t)
           (or (= (roadway_kind r) RK_Highway)
               true))
      (yield_right_of_way_to_pedestrian v_entering t)))

I need to reconsider - `yield_right_of_way_to_pedestrian` is for pedestrians, not vehicles. Let me look at the schema more carefully for yielding to vehicles.

The schema doesn't have a direct `yield_right_of_way_to_vehicle` predicate, but the rule essentially means the entering vehicle must not proceed if it would create an immediate hazard or not have assured clear distance. Let me use `movement_can_be_made_safely` as the constraint - the vehicle must not enter/cross unless it's safe given the approaching vehicle.

(forall ((v_entering Vehicle) (v_approaching Vehicle) (a Access) (r Roadway) (t Int))
  (=> (and (not (= v_entering v_approaching))
           (emerging_from v_entering a t)
           (access_on_roadway a r)
           (or (= (access_kind a) AK_Alley)
               (= (access_kind a) AK_Building)
               (= (access_kind a) AK_PrivateRoad)
               (= (access_kind a) AK_Driveway))
           (on_roadway v_approaching r t))
      (and (not (is_immediate_hazard v_entering v_approaching
                  (let ((dummy_int 0)) dummy_int) t)))))

Let me provide a clean, correct encoding:

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
           (movement_can_be_made_safely v_entering t))))