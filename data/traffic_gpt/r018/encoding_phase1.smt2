(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (= (approach_kind v r t) APK_IntersectionOrRailInMunicipality_100ft))
      (not (= (roadway_pos v r t) RP_LeftHalf))))