(forall ((p Person) (a Animal) (t Int))
  (=>
    (and (is_kind a AK_Fin) (exists ((shark Animal)) (and (is_kind shark AK_Shark) (is_part_of a shark))))
    (not
      (or
        (and (is_kind a AK_Fin)
             (exists ((shark Animal)) (and (is_kind shark AK_Shark) (is_part_of a shark)))
             (not (fin_destroyed a t)))
        (buys p a t)
        (offers_to_buy p a t)
        (sells p a t)
        (offers_to_sell p a t)
        (and (possesses p a t) (for_sale p a t))
        (and (transports p a t) (for_sale p a t))
        (and (ships p a t) (for_sale p a t))
        (advertises_for_sale p a t)))))