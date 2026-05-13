(forall ((v_follower Vehicle) (v_leader Vehicle) (t Int))
  (=> (following v_follower v_leader t)
      (and (assured_clear_distance v_follower v_leader t)
           (can_safely_stop v_follower t))))