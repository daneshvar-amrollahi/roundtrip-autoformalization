(forall ((p Person) (a Animal) (t Int))
  (=> (and (captures_by_nonlethal_means p a t)
           (or (is_kind a AK_Reptile) (is_kind a AK_Amphibian)))
      (and
        (or (on_road_shoulder p t)
            (exists ((row Land))
              (and (on_land p row t)
                   (land_kind row LK_RightOfWay))))
        (or
          (and (has_document_kind p DOK_ReptileAmphibianStamp t)
               (forall ((d Device))
                 (=> (uses_device p d t)
                     (not (device_kind d DK_CrabTrap)))))
          (has_subchapter_authorization p t)))))