(forall ((v Vehicle) (u Vehicle) (i Intersection) (t Int))
  (=> (and (approaching_intersection v i t)
           (= (intersection_control i) IC_YieldSign)
           (not (= v u))
           (or (in_intersection u i t)
               (is_immediate_hazard u v i t)))
      (and (reduced_speed_appropriate v t)
           (yield_right_of_way_to_pedestrian v t))))

SCHEMA_INSUFFICIENT: The schema lacks a general vehicle-to-vehicle yield predicate `yield_right_of_way (Vehicle Vehicle Int) Bool`. The schema only provides `yield_right_of_way_to_pedestrian (Vehicle Int) Bool` for pedestrians. There is no `yield_right_of_way v u t` predicate for yielding to another vehicle. The closest approximation using available predicates would be:

(forall ((v Vehicle) (u Vehicle) (i Intersection) (t Int))
  (=> (and (approaching_intersection v i t)
           (= (intersection_control i) IC_YieldSign)
           (not (= v u))
           (or (in_intersection u i t)
               (is_immediate_hazard u v i t)))
      (and (reduced_speed_appropriate v t)
           (not (entering_intersection v i t)))))