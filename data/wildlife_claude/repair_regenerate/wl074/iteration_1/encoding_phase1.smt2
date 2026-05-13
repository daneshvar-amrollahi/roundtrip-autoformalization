(forall ((p Person) (a Animal) (t Int))
  (=>
    (and
      (is_kind a AK_Fin)
      (exists ((s Animal)) (and (is_kind s AK_Shark) (is_part_of a s)))
    )
    (or
      (and
        (not
          (or
            (and (possesses p a t) (not (fin_destroyed a t)))
            (and (buys p a t))
            (and (offers_to_buy p a t))
            (and (sells p a t))
            (and (offers_to_sell p a t))
            (and (possesses p a t) (for_sale p a t))
            (and (transports p a t) (for_sale p a t))
            (and (ships p a t) (for_sale p a t))
            (and (advertises_for_sale p a t))
          )
        )
      )
      false
    )
  )
)