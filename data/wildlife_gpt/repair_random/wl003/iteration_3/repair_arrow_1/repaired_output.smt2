(exists ((p Person) (a Animal) (t Int) (d Document))
  (and
    (captures_by_nonlethal_means p a t)
    (or (is_kind a AK_Reptile) (is_kind a AK_Amphibian))
    (or (on_road_shoulder p t) (on_road_or_right_of_way p t))
    (or
      (and
        (has_document p d t)
        (document_kind d DOK_ReptileAmphibianStamp)
        (forall ((trap Device))
          (not (uses_device p trap t))))
      (has_subchapter_authorization p t))))