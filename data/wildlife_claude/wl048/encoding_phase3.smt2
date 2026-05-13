(forall ((p Person) (d Device) (t Int))
  (=> (device_kind d DK_ElectricityDevice)
      (and (not (manufactures_device p d t))
           (not (sells_device p d t)))))