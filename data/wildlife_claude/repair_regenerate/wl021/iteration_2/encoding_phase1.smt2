(forall ((d Document) (grantee Person) (grantor Person) (l Land) (t Int))
  (=> (is_valid_consent d grantee grantor t)
      (and
        (names_grantee d grantee)
        (identifies_land d l)
        (signed_by d grantor)
        (or (is_landowner_of grantor l)
            (is_agent_of grantor grantor))
        (shows_address_and_phone_of d grantor))))