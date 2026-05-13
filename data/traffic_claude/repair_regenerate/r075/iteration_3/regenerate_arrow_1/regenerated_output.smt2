(forall ((v Vehicle) (ev Vehicle) (t Int))
  (=> (and (not (= v ev))
           (is_authorized_emergency_vehicle ev)
           (emergency_vehicle_approaching ev v t)
           (emergency_signals_active ev t))
      (yield_right_of_way_to_pedestrian v t)))

Wait - `yield_right_of_way_to_pedestrian` is not the right predicate for yielding to an emergency vehicle. Let me reconsider the schema.

Looking at the schema more carefully, there isn't a general `yield_right_of_way` predicate - there's `yield_right_of_way_to_pedestrian` for pedestrians. For emergency vehicles, the schema provides `emergency_vehicle_approaching`, `emergency_signals_active`, and `vacated_nearest_lane`. The rule says the operator "shall yield the right-of-way" which in the emergency vehicle context maps to stopping/pulling over behavior. The closest encoding uses `is-stopping` or `is-decelerating` combined with `vacated_nearest_lane`.

Let me provide the proper encoding:

(forall ((v Vehicle) (ev Vehicle) (t Int))
  (=> (and (not (= v ev))
           (is_authorized_emergency_vehicle ev)
           (emergency_vehicle_approaching ev v t)
           (emergency_signals_active ev t))
      (vacated_nearest_lane v ev t)))