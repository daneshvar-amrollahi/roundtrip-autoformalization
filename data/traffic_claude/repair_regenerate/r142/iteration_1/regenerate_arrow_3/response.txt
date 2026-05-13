(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and
        (on_roadway v r t)
        (or
          (approach_kind v r t) = APK_IntersectionOrRailInMunicipality_100ft
        )
        (or
          (intends_turn v TD_Left t)
          (executing_turn v TD_Left t)
        )
        (exists ((a Access))
          (and
            (access_on_roadway a r)
            (or
              (= (access_kind a) AK_Alley)
              (= (access_kind a) AK_PrivateRoad)
              (= (access_kind a) AK_Driveway)
            )
            (or
              (turning_into v a t)
              (emerging_from v a t)
            )
          )
        )
      )
      (divider_crossing_allowed v r t)))