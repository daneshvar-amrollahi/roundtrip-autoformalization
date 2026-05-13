(forall ((v Vehicle) (u Vehicle) (i Intersection) (t Int))
  (=> (and (is_ego v)
           (not (= v u))
           (approaching_intersection v i t)
           (= (intersection_control i) IC_YieldSign)
           (or (in_intersection u i t)
               (is_immediate_hazard u v i t)))
      (and (reduced_speed_appropriate v t)
           (yield_right_of_way v u t))))

SCHEMA_INSUFFICIENT: The schema lacks a `yield_right_of_way` predicate that relates two vehicles (i.e., `(yield_right_of_way Vehicle Vehicle Int) Bool`). The schema only provides `yield_right_of_way_to_pedestrian` for pedestrians. However, I have used `yield_right_of_way` as the closest semantic encoding per the diagnostic feedback requiring a vehicle-yielding predicate referencing the other vehicle `u`.