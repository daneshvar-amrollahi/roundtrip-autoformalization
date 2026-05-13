(forall ((t Int))
  (forall ((r_unpaved Roadway) (r_paved Roadway) (i Intersection))
    (let ((ego Vehicle))
      (forall ((v Vehicle))
        (=> (and (is_ego ego)
                 (on_roadway ego r_unpaved t)
                 (not (roadway_is_paved r_unpaved))
                 (roadway_is_paved r_paved)
                 (intersection_on_roadway i r_unpaved)
                 (intersection_on_roadway i r_paved)
                 (approaching_intersection ego i t))
            (and
              ;; must stop
              (stopped ego t)

              ;; must not enter the intersection while any vehicle on the paved roadway
              ;; that is in or approaching the intersection constitutes an immediate hazard
              (=> (exists ((v2 Vehicle))
                    (and (not (= v2 ego))
                         (on_roadway v2 r_paved t)
                         (or (in_intersection v2 i t)
                             (approaching_intersection v2 i t))
                         (is_immediate_hazard v2 ego i t)))
                  (not (entering_intersection ego i t)))

              ;; must maintain assured clear distance ahead of any such vehicle
              (=> (and (not (= v ego))
                       (on_roadway v r_paved t)
                       (or (in_intersection v i t)
                           (approaching_intersection v i t))
                       (is_immediate_hazard v ego i t))
                  (assured_clear_distance ego v t))))))))