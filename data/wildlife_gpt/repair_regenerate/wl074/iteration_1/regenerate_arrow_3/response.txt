(or
  (exists ((p Person) (fin Animal) (t Int))
    (and
      (possesses p fin t)
      (is_kind fin AK_Fin)
      (is_part_of fin fin)
      (not (fin_destroyed fin t))))
  (exists ((p Person) (fin Animal) (t Int))
    (and
      (is_kind fin AK_Fin)
      (or
        (buys p fin t)
        (offers_to_buy p fin t)
        (sells p fin t)
        (offers_to_sell p fin t)
        (advertises_for_sale p fin t)
        (and (possesses p fin t) (for_sale p fin t))
        (and (transports p fin t) (for_sale p fin t))
        (and (ships p fin t) (for_sale p fin t))))))
  (exists ((p Person) (t Int))
    (and
      (has_subchapter_authorization p t)
      (not (authorized_by_commission p t)))))