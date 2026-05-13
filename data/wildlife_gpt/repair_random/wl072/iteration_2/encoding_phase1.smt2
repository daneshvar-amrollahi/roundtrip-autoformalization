(forall ((p Person) (fish Animal) (t Int))
  (=>
    (and
      (possesses p fish t)
      (is_kind fish AK_Finfish)
      (has_tail_removed fish)
      (exists ((w WaterBody) (t_take Int))
        (and
          (takes p fish t_take)
          (on_water_body p w t_take)
          (water_kind w WK_CoastalWater)))
      (not (is_kind fish AK_Other))
      (not (is_kind fish AK_Shark))
      (not (is_kind fish AK_Finfish))
      (not
        (and
          (has_been_finally_processed fish t)
          (or
            (delivered_to_final_destination fish t)
            (delivered_to_certified_dealer fish t)))))
    (not (possesses p fish t))))