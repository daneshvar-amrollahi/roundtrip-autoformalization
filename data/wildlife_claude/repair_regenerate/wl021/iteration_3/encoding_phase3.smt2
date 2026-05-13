(forall ((doc Document) (grantor Person) (grantee Person) (t Int))
  (=> (is_valid_consent doc grantor grantee t)
      (exists ((l Land))
        (and
          (names_grantee doc grantee)
          (identifies_land doc l)
          (signed_by doc grantor)
          (shows_address_and_phone_of doc grantor)
          (exists ((owner Person))
            (and
              (is_landowner_of owner l)
              (or
                (= grantor owner)
                (is_agent_of grantor owner)
                (is_employee_of grantor owner))))))))