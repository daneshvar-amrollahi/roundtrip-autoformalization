(forall ((p Person) (f Animal) (t Int))
  (=> (and (possesses p f t)
           (is_kind f AK_Fish)
           (is_named_in_protected_fish_list f))
      (commits_offense p t
        (or
          (not (exists ((doc Document))
                 (and (document_kind doc DOK_OriginVerification)
                      (keeps_with p doc f t))))
          (exists ((doc Document) (emp Person))
            (and (document_kind doc DOK_OriginVerification)
                 (is_department_employee emp t)
                 (requests emp p doc t)
                 (not (displays_on_request p doc t))))))))