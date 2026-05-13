(forall ((v_emerging Vehicle) (a Access) (r Roadway) (v_approaching Vehicle) (t Int))
  (=> (and (emerging_from v_emerging a t)
           (or (= (access_kind a) AK_Alley)
               (= (access_kind a) AK_Driveway)
               (= (access_kind a) AK_Building))
           (access_on_roadway a r)
           (on_roadway v_emerging r t)
           (not (= v_emerging v_approaching))
           (approaching_opposite v_approaching v_emerging t))
      (yield_right_of_way_to_pedestrian v_emerging t)))

Wait, let me reconsider. The rule says "yield the right-of-way to an approaching vehicle", not pedestrian. Let me check the schema for a vehicle yield predicate.

The schema has `yield_right_of_way_to_pedestrian` but no general `yield_right_of_way_to_vehicle`. However, yielding right-of-way to an approaching vehicle can be approximated: the emerging vehicle must not enter the roadway in a way that creates a hazard - it must ensure assured clear distance and allow the approaching vehicle to pass safely.

Let me re-examine. The schema has `assured_clear_distance`, `movement_can_be_made_safely`, and `is_immediate_hazard`. The best encoding given schema constraints:

(forall ((v_emerging Vehicle) (a Access) (r Roadway) (v_approaching Vehicle) (t Int))
  (=> (and (emerging_from v_emerging a t)
           (or (= (access_kind a) AK_Alley)
               (= (access_kind a) AK_Driveway)
               (= (access_kind a) AK_Building))
           (access_on_roadway a r)
           (on_roadway v_approaching r t)
           (not (= v_emerging v_approaching))
           (approaching_opposite v_approaching v_emerging t))
      (not (entering_intersection v_emerging
             (let ((dummy Intersection)) dummy) t))))

That's wrong too. Let me provide the cleanest encoding possible:

(forall ((v_emerging Vehicle) (a Access) (r Roadway) (v_approaching Vehicle) (t Int))
  (=> (and (emerging_from v_emerging a t)
           (or (= (access_kind a) AK_Alley)
               (= (access_kind a) AK_Driveway)
               (= (access_kind a) AK_Building))
           (access_on_roadway a r)
           (on_roadway v_approaching r t)
           (not (= v_emerging v_approaching))
           (approaching_opposite v_approaching v_emerging t))
      (assured_clear_distance v_emerging v_approaching t)))