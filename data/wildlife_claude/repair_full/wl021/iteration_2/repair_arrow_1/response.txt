(forall ((doc Document) (grantor Person) (grantee Person) (t Int))
  (=> (is_valid_consent doc grantor grantee t)
      (and
        (document_kind doc DOK_WrittenConsent)
        (names_grantee doc grantee)
        (exists ((l Land) (signer Person))
          (and
            (identifies_land doc l)
            (signed_by doc signer)
            (or
              (is_landowner_of signer l)
              (is_agent_of signer grantor)
              (exists ((owner Person))
                (and
                  (is_landowner_of owner l)
                  (or
                    (is_agent_of signer owner)
                    (is_employee_of signer owner)))))
            (shows_address_and_phone_of doc signer))))))