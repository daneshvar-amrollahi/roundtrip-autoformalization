(forall ((r Roadway) (t Int))
  (=> (and (= (roadway_kind r) RK_Beach)
           (speed_limit_posted r t))
      (= (speed_limit_value r t) mph_15)))