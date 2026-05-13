(forall ((p Person) (d Device) (w WaterBody) (t Int))
  (=> (and (possesses_device p d t)
           (on_water_body p w t)
           (water_kind w WK_PublicWater)
           (not (is_permitted_by_code d t)))
      (not
        (and
          (exists ((v Device))
            (and (device_kind v DK_FloatingDevice)
                 (inside_device p v t)
                 (on_water_body p w t)
                 (water_kind w WK_PublicCoastalWater)
                 (on_device d v t)))
          (or
            (in_port p t)
            (and (in_marked_channel p t)
                 (going_directly_to_or_from_permitted_public_water p d t)))))))