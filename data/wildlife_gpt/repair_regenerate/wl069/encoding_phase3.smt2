(forall ((p Person) (sg Animal) (t Int))
  (=> (and (uproots_or_digs_by_propeller p sg t)
           (is_kind sg AK_Seagrass))
      (has_commercial_seagrass_permit p t)))