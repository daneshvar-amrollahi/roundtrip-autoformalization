(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (= (roadway_access_control r) AC_Limited))
      (not (backing v t))))