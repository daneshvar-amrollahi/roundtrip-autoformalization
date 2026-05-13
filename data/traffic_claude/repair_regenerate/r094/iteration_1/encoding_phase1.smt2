(forall ((v Vehicle) (t Int) (i Intersection))
  (=> (and (is_ego v)
           (in_intersection v i t)
           (pedestrian_present_in_crosswalk i t))
      (not (or (= (stop_action v t) SA_Stop)
               (= (stop_action v t) SA_Stand)
               (= (stop_action v t) SA_Park)))))

Wait, let me reconsider. The rule says "on a crosswalk" — this is about the physical location of a crosswalk, not necessarily requiring pedestrians to be present. Let me re-examine the schema.

The schema has `pedestrian_present_in_crosswalk` which ties crosswalks to intersections, and `dist_to_feature` with `PF_Crosswalk`. The rule is a blanket prohibition on stopping/standing/parking on a crosswalk. The closest encoding uses the proximity feature for crosswalks — being at distance essentially zero from a crosswalk means being on it.

Let me provide a cleaner encoding:

(forall ((v Vehicle) (t Int))
  (=> (is_ego v)
      (not (and (or (= (stop_action v t) SA_Stop)
                    (= (stop_action v t) SA_Stand)
                    (= (stop_action v t) SA_Park))
                (<= (dist_to_feature v PF_Crosswalk t) ft_5_sq)))))

Hmm, but `dist_to_feature` returns Real (likely linear feet, not squared), and being "on" a crosswalk means essentially zero distance. Let me use a cleaner approach:

(forall ((v Vehicle) (t Int))
  (=> (and (is_ego v)
           (or (= (stop_action v t) SA_Stop)
               (= (stop_action v t) SA_Stand)
               (= (stop_action v t) SA_Park)))
      (> (dist_to_feature v PF_Crosswalk t) 0.0)))