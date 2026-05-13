(forall ((doc Document) (grantee Person) (owner Person) (t Int))
  (=> (is_valid_consent doc grantee owner t)
      (and
        (document_kind doc DOK_WrittenConsent)
        (names_grantee doc grantee)
        (exists ((l Land))
          (identifies_land doc l))
        (exists ((signer Person))
          (and
            (signed_by doc signer)
            (or
              (is_landowner_of signer l)
              (is_agent_of signer owner)
              (is_employee_of signer owner))
            (shows_address_and_phone_of doc signer))))))