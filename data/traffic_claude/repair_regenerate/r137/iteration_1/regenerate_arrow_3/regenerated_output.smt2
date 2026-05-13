(forall ((v Vehicle) (i Intersection) (t Int))
  (=> (or (executing_turn_at_intersection v TD_Left i t)
          (executing_turn_at_intersection v TD_Right i t))
      (not (cutting_through_property v i t))))