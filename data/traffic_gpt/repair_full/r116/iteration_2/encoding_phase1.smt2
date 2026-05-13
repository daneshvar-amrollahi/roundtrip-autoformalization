(forall ((r Roadway) (t Int))
  (=> (= (roadway_kind r) RK_Beach)
      (= (speed_limit_value r t) mph_15)))