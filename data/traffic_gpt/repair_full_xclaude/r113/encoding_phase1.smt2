(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (= (district_of_roadway r) DK_Urban)
           (not (special_hazard_exists v r t)))
      (and
        (=> (not (= (roadway_kind r) RK_Alley))
            (<= (velocity v t) mph_30))
        (=> (= (roadway_kind r) RK_Alley)
            (<= (velocity v t) mph_15)))))