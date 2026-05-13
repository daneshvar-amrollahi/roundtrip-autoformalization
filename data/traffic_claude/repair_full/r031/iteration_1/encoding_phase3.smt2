(forall ((v_leader Vehicle) (t Int))
  (=> (and (is_ego v_leader false)
           (exists ((v_ego Vehicle))
             (and (is_ego v_ego)
                  (following v_ego v_leader t))))
      (forall ((v_ego Vehicle))
        (=> (and (is_ego v_ego)
                 (following v_ego v_leader t))
            (and (assured_clear_distance v_ego v_leader t)
                 (can_safely_stop v_ego t))))))

Let me reconsider and simplify this encoding:

(forall ((v_ego Vehicle) (v_leader Vehicle) (t Int))
  (=> (and (is_ego v_ego)
           (not (= v_ego v_leader))
           (following v_ego v_leader t))
      (and (assured_clear_distance v_ego v_leader t)
           (can_safely_stop v_ego t))))