(forall ((v Vehicle) (i Intersection) (t Int))
  (=> (or (intends_turn v TD_Left t)
          (intends_turn v TD_Right t))
      (not (cutting_through_property v i t))))