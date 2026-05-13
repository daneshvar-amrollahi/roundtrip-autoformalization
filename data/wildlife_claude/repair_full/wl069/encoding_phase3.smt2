(forall ((p Person) (a Animal) (t Int))
  (=> (and (uproots_or_digs_by_propeller p a t)
           (is_kind a AK_Seagrass))
      (has_commercial_seagrass_permit p t)))