(forall ((p Person) (f Animal) (t Int))
  (=> (and (possesses p f t)
           (is_kind f AK_Fish)
           (is_named_in_protected_fish_list f))
      (not
        (exists ((doc Document))
          (and (document_kind doc DOK_OriginVerification)
               (keeps_with p doc f t)
               (displays_on_request p doc t))))))