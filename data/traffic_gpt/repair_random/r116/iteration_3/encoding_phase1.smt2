(forall ((r Roadway) (t Int))
  (=> (= (roadway_kind r) RK_Beach)
      (and (speed_limit_posted r t)
           (= (speed_limit_value r t) mph_15))))