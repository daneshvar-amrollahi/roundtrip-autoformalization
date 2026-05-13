(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (= (roadway_flow r) FK_OneWay)
      (= (approach_kind v r t) APK_None)))