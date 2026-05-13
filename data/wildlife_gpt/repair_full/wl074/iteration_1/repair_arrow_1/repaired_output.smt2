(or
  (exists ((p Person) (fin Animal) (t Int))
    (and
      (is_kind fin AK_Fin)
      (not (fin_destroyed fin t))))
  (exists ((p Person) (fin Animal) (t Int))
    (and
      (is_kind fin AK_Fin)
      (or
        (buys p fin t)
        (offers_to_buy p fin t)
        (sells p fin t)
        (offers_to_sell p fin t)
        (and (possesses p fin t) (for_sale p fin t))
        (and (transports p fin t) (for_sale p fin t))
        (and (ships p fin t) (for_sale p fin t))
        (advertises_for_sale p fin t))))
  (exists ((p Person) (t Int))
    (and
      (not (has_subchapter_authorization p t))
      (or (is_hunting p t) (fishes p (let ((a Animal)) a) t)))))