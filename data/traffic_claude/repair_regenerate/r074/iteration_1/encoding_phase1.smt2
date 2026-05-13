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

I need to reconsider - the schema doesn't have a general "yield right of way to vehicle" predicate. Let me look more carefully.

Looking at the schema again, I see `yield_right_of_way_to_pedestrian` but no general yield-to-vehicle predicate. However, the rule is about yielding to vehicles. The closest encoding would use `is_immediate_hazard` or movement safety predicates. Let me reconsider using available predicates to capture the semantics.

The best approximation: the entering vehicle must not proceed (must stop/not enter) when an approaching vehicle is present - encoded via `movement_can_be_made_safely` or ensuring the vehicle stops.

(forall ((v_entering Vehicle) (v_approaching Vehicle) (a Access) (r Roadway) (t Int))
  (=> (and (not (= v_entering v_approaching))
           (emerging_from v_entering a t)
           (access_on_roadway a r)
           (or (= (access_kind a) AK_Alley)
               (= (access_kind a) AK_Building)
               (= (access_kind a) AK_PrivateRoad)
               (= (access_kind a) AK_Driveway))
           (on_roadway v_approaching r t))
      (and (not (movement_can_be_made_safely v_entering t))
           (=> (not (safe-distance v_entering v_approaching t))
               (is-stopping v_entering t)))))

Hmm, that's not clean either. Let me provide the most faithful encoding:

(forall ((v_entering Vehicle) (v_approaching Vehicle) (a Access) (r Roadway) (t Int))
  (=> (and (not (= v_entering v_approaching))
           (emerging_from v_entering a t)
           (access_on_roadway a r)
           (or (= (access_kind a) AK_Alley)
               (= (access_kind a) AK_Building)
               (= (access_kind a) AK_PrivateRoad)
               (= (access_kind a) AK_Driveway))
           (on_roadway v_approaching r t)
           (not (safe-distance v_entering v_approaching t)))
      (is-stopping v_entering t)))