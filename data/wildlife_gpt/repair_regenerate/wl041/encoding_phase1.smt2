(or
  (exists ((official Person) (wolf Animal) (t Int))
    (and
      (transports official wolf t)
      (is_kind wolf AK_Wolf)
      (is_state_or_county_official official)
      (on_official_duty official t)))
  (exists ((holder Person) (wolf Animal) (t Int))
    (and
      (is_kind wolf AK_Wolf)
      (or (possesses holder wolf t) (transports holder wolf t))
      (or (is_licensed_circus_zoo_owner holder)
          (exists ((owner Person))
            (and (is_licensed_circus_zoo_owner owner)
                 (is_agent_of holder owner))))
      (or (for_exhibition holder t)
          (for_scientific_purpose holder t)))))