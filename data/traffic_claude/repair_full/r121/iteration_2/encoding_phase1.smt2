(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (> (velocity v t) 0.0)
           (or (= (roadway_kind r) RK_MountainHighway)
               (= (roadway_kind r) RK_Tunnel)
               (= (roadway_kind r) RK_Other)))
      (and (vehicle_under_control v t)
           (close_to_right_edge_practicable v r t))))

SCHEMA_INSUFFICIENT: The schema lacks dedicated RoadwayKind values for defiles (RK_Defile) and canyons (RK_Canyon). The closest available alternatives are RK_Tunnel and RK_Other, which are imprecise substitutes. Ideally, the enumeration should include RK_Defile and RK_Canyon to faithfully encode this rule.